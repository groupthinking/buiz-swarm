"""
Billing Service - Revenue tracking and platform fee management.

Handles:
- Revenue tracking for companies
- Platform fee calculation (20% revenue share)
- Stripe Connect integration
- Payouts to companies
- Billing reports
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP

from ..models.company import Company
from ..config import settings

logger = logging.getLogger(__name__)


class BillingService:
    """
    Service for managing billing and revenue sharing.
    
    Implements the 20% revenue share model where BuizSwarm takes 20%
    of company revenue and passes 80% to the company.
    """
    
    PLATFORM_FEE_PERCENT = Decimal("20.00")  # 20% platform fee
    
    def __init__(self):
        self._transactions: List[Dict[str, Any]] = []  # In-memory store
    
    async def record_revenue(
        self,
        company: Company,
        amount: float,
        source: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record revenue for a company and calculate platform fees.
        
        Args:
            company: Company that earned revenue
            amount: Revenue amount
            source: Source of revenue (e.g., "stripe_payment", "manual")
            description: Optional description
            metadata: Optional additional metadata
            
        Returns:
            Transaction details with fee breakdown
        """
        amount_decimal = Decimal(str(amount))
        
        # Calculate fees
        platform_fee = (amount_decimal * self.PLATFORM_FEE_PERCENT / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        net_revenue = amount_decimal - platform_fee
        
        # Create transaction record
        transaction = {
            "id": f"txn_{len(self._transactions)}",
            "company_id": company.id,
            "amount": float(amount_decimal),
            "platform_fee": float(platform_fee),
            "net_revenue": float(net_revenue),
            "platform_fee_percent": float(self.PLATFORM_FEE_PERCENT),
            "source": source,
            "description": description,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
        self._transactions.append(transaction)
        
        # Update company totals
        company.total_revenue_processed += float(amount_decimal)
        company.platform_fees_paid += float(platform_fee)
        
        # Update metrics
        company.metrics.total_revenue = company.total_revenue_processed
        company.metrics.revenue_this_month += float(amount_decimal)
        
        logger.info(
            f"Recorded revenue for company {company.id}: "
            f"${amount} (fee: ${platform_fee}, net: ${net_revenue})"
        )
        
        return transaction
    
    async def process_stripe_payment(
        self,
        company: Company,
        payment_intent_id: str,
        amount: float,
        currency: str = "usd"
    ) -> Dict[str, Any]:
        """
        Process a Stripe payment and handle revenue sharing.
        
        Args:
            company: Company receiving payment
            payment_intent_id: Stripe PaymentIntent ID
            amount: Payment amount
            currency: Currency code
            
        Returns:
            Transaction details
        """
        # Create transfer to connected account (80% to company)
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            amount_decimal = Decimal(str(amount))
            net_revenue = amount_decimal * (Decimal("100") - self.PLATFORM_FEE_PERCENT) / Decimal("100")
            
            # Record the revenue
            transaction = await self.record_revenue(
                company=company,
                amount=amount,
                source="stripe_payment",
                description=f"Stripe payment {payment_intent_id}",
                metadata={
                    "payment_intent_id": payment_intent_id,
                    "currency": currency
                }
            )
            
            # Transfer net revenue to company's connected account
            if company.infrastructure.stripe_account_id:
                transfer = stripe.Transfer.create(
                    amount=int(net_revenue * 100),  # Convert to cents
                    currency=currency,
                    destination=company.infrastructure.stripe_account_id,
                    metadata={
                        "company_id": company.id,
                        "payment_intent_id": payment_intent_id,
                        "transaction_id": transaction["id"]
                    }
                )
                
                transaction["transfer_id"] = transfer.id
                transaction["transfer_status"] = transfer.status
            
            return transaction
            
        except Exception as e:
            logger.error(f"Stripe payment processing error: {e}")
            return {
                "error": str(e),
                "payment_intent_id": payment_intent_id,
                "status": "failed"
            }
    
    async def get_company_transactions(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a company.
        
        Args:
            company_id: Company ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of transactions
            
        Returns:
            List of transactions
        """
        transactions = [
            t for t in self._transactions
            if t["company_id"] == company_id
        ]
        
        if start_date:
            transactions = [
                t for t in transactions
                if datetime.fromisoformat(t["created_at"]) >= start_date
            ]
        
        if end_date:
            transactions = [
                t for t in transactions
                if datetime.fromisoformat(t["created_at"]) <= end_date
            ]
        
        # Sort by date descending
        transactions.sort(
            key=lambda t: t["created_at"],
            reverse=True
        )
        
        return transactions[:limit]
    
    async def get_company_billing_summary(
        self,
        company: Company,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        Get billing summary for a company.
        
        Args:
            company: Company to get summary for
            period: Period type (day, week, month, year)
            
        Returns:
            Billing summary
        """
        # Calculate period dates
        now = datetime.utcnow()
        
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "year":
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=30)
        
        # Get transactions for period
        transactions = await self.get_company_transactions(
            company.id,
            start_date=start_date
        )
        
        # Calculate totals
        total_revenue = sum(t["amount"] for t in transactions)
        total_fees = sum(t["platform_fee"] for t in transactions)
        total_net = sum(t["net_revenue"] for t in transactions)
        
        return {
            "period": period,
            "period_start": start_date.isoformat(),
            "period_end": now.isoformat(),
            "transaction_count": len(transactions),
            "total_revenue": total_revenue,
            "total_platform_fees": total_fees,
            "total_net_revenue": total_net,
            "platform_fee_percent": float(self.PLATFORM_FEE_PERCENT),
            "lifetime_revenue": company.total_revenue_processed,
            "lifetime_platform_fees": company.platform_fees_paid
        }
    
    async def get_platform_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get platform-wide billing summary.
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Platform billing summary
        """
        transactions = self._transactions
        
        if start_date:
            transactions = [
                t for t in transactions
                if datetime.fromisoformat(t["created_at"]) >= start_date
            ]
        
        if end_date:
            transactions = [
                t for t in transactions
                if datetime.fromisoformat(t["created_at"]) <= end_date
            ]
        
        total_revenue = sum(t["amount"] for t in transactions)
        total_fees = sum(t["platform_fee"] for t in transactions)
        
        # Group by company
        company_revenue: Dict[str, float] = {}
        for t in transactions:
            company_id = t["company_id"]
            company_revenue[company_id] = company_revenue.get(company_id, 0) + t["amount"]
        
        return {
            "total_transactions": len(transactions),
            "total_gmv": total_revenue,  # Gross Merchandise Value
            "total_platform_revenue": total_fees,
            "active_companies": len(company_revenue),
            "top_companies": sorted(
                [{"company_id": k, "revenue": v} for k, v in company_revenue.items()],
                key=lambda x: x["revenue"],
                reverse=True
            )[:10]
        }
    
    async def create_payout(
        self,
        company: Company,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a payout to a company's connected account.
        
        Args:
            company: Company to payout
            amount: Optional specific amount (defaults to available balance)
            
        Returns:
            Payout details
        """
        if not company.infrastructure.stripe_account_id:
            return {"error": "Company has no Stripe connected account"}
        
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Get available balance
            if amount is None:
                balance = stripe.Balance.retrieve(
                    stripe_account=company.infrastructure.stripe_account_id
                )
                available = balance.available[0].amount if balance.available else 0
                amount = available / 100  # Convert from cents
            
            if amount <= 0:
                return {"error": "No available balance for payout"}
            
            # Create payout
            payout = stripe.Payout.create(
                amount=int(amount * 100),
                currency="usd",
                stripe_account=company.infrastructure.stripe_account_id
            )
            
            return {
                "success": True,
                "payout_id": payout.id,
                "amount": amount,
                "status": payout.status,
                "arrival_date": payout.arrival_date
            }
            
        except Exception as e:
            logger.error(f"Payout creation error: {e}")
            return {"error": str(e)}
    
    async def generate_invoice(
        self,
        company: Company,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Generate an invoice for a company.
        
        Args:
            company: Company to invoice
            period_start: Invoice period start
            period_end: Invoice period end
            
        Returns:
            Invoice details
        """
        transactions = await self.get_company_transactions(
            company.id,
            start_date=period_start,
            end_date=period_end
        )
        
        total_revenue = sum(t["amount"] for t in transactions)
        total_fees = sum(t["platform_fee"] for t in transactions)
        
        invoice = {
            "invoice_id": f"INV-{company.id}-{period_start.strftime('%Y%m')}",
            "company_id": company.id,
            "company_name": company.name,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "line_items": [
                {
                    "description": "Platform Fee (20% of revenue)",
                    "quantity": 1,
                    "unit_price": total_fees,
                    "total": total_fees
                }
            ],
            "subtotal": total_fees,
            "tax": 0,
            "total": total_fees,
            "transaction_count": len(transactions),
            "gross_revenue": total_revenue
        }
        
        return invoice
    
    async def handle_stripe_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.
        
        Args:
            payload: Webhook payload
            signature: Stripe signature header
            
        Returns:
            Processing result
        """
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            
            if event["type"] == "payment_intent.succeeded":
                payment_intent = event["data"]["object"]
                
                # Find company by connected account
                company_id = payment_intent.get("metadata", {}).get("company_id")
                
                if company_id:
                    # Process payment
                    from .company_service import get_company_service
                    company_service = get_company_service()
                    company = await company_service.get_company(company_id)
                    
                    if company:
                        await self.process_stripe_payment(
                            company=company,
                            payment_intent_id=payment_intent["id"],
                            amount=payment_intent["amount"] / 100,
                            currency=payment_intent["currency"]
                        )
                
                return {"success": True, "event": event["type"]}
            
            elif event["type"] == "account.updated":
                account = event["data"]["object"]
                # Handle account updates
                return {"success": True, "event": event["type"]}
            
            else:
                return {"success": True, "event": event["type"], "handled": False}
                
        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            return {"error": str(e)}


# Global service instance
_billing_service: Optional[BillingService] = None


def get_billing_service() -> BillingService:
    """Get or create global billing service."""
    global _billing_service
    if _billing_service is None:
        _billing_service = BillingService()
    return _billing_service
