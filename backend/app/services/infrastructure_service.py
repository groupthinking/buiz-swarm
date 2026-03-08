"""
Infrastructure Service - Provision and manage company infrastructure.

Handles provisioning of:
- Web servers (Render, AWS, Vercel)
- Databases (Neon, AWS RDS, Supabase)
- Email accounts (SendGrid, AWS SES)
- GitHub repositories
- Stripe accounts
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx

from ..models.company import Company, InfrastructureConfig
from ..config import settings

logger = logging.getLogger(__name__)


class InfrastructureService:
    """
    Service for provisioning and managing company infrastructure.
    
    Integrates with various cloud providers to set up complete
    infrastructure stacks for companies.
    """
    
    def __init__(self):
        self._http_client = httpx.AsyncClient(timeout=60.0)
    
    async def provision_all(self, company: Company) -> Dict[str, Any]:
        """
        Provision all infrastructure for a company.
        
        Args:
            company: Company to provision infrastructure for
            
        Returns:
            Provisioning results
        """
        results = {
            "web_server": None,
            "database": None,
            "email": None,
            "github": None,
            "stripe": None
        }
        
        try:
            # Provision web server
            results["web_server"] = await self.provision_web_server(company)
            
            # Provision database
            results["database"] = await self.provision_database(company)
            
            # Provision email
            results["email"] = await self.provision_email(company)
            
            # Create GitHub repo
            results["github"] = await self.create_github_repo(company)
            
            # Setup Stripe
            results["stripe"] = await self.setup_stripe(company)
            
            logger.info(f"Completed infrastructure provisioning for company {company.id}")
            
        except Exception as e:
            logger.error(f"Infrastructure provisioning error: {e}")
            results["error"] = str(e)
        
        return results
    
    async def provision_web_server(
        self,
        company: Company,
        provider: str = "render"
    ) -> Dict[str, Any]:
        """
        Provision a web server for the company.
        
        Args:
            company: Company to provision for
            provider: Provider to use (render, aws, vercel)
            
        Returns:
            Provisioning result
        """
        logger.info(f"Provisioning web server for {company.name} via {provider}")
        
        if provider == "render":
            return await self._provision_render_service(company)
        elif provider == "aws":
            return await self._provision_aws_service(company)
        elif provider == "vercel":
            return await self._provision_vercel_service(company)
        else:
            return {"error": f"Unknown provider: {provider}"}
    
    async def _provision_render_service(self, company: Company) -> Dict[str, Any]:
        """Provision service on Render."""
        if not settings.RENDER_API_KEY:
            return {"error": "Render API key not configured"}
        
        try:
            # This is a placeholder - actual Render API integration would go here
            # Render API: https://render.com/docs/api
            
            service_name = f"{company.slug}-app"
            
            response = await self._http_client.post(
                "https://api.render.com/v1/services",
                headers={"Authorization": f"Bearer {settings.RENDER_API_KEY}"},
                json={
                    "type": "web_service",
                    "name": service_name,
                    "ownerId": company.owner_id,
                    "env": "python",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT"
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Update company infrastructure
                company.infrastructure.web_server_provider = "render"
                company.infrastructure.web_server_url = data.get("service", {}).get("url")
                company.infrastructure.web_server_status = "provisioned"
                
                return {
                    "success": True,
                    "provider": "render",
                    "service_name": service_name,
                    "url": data.get("service", {}).get("url")
                }
            else:
                return {
                    "success": False,
                    "error": f"Render API error: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Render provisioning error: {e}")
            return {"error": str(e)}
    
    async def _provision_aws_service(self, company: Company) -> Dict[str, Any]:
        """Provision service on AWS (Elastic Beanstalk or ECS)."""
        # This would use boto3 to provision AWS resources
        # Placeholder implementation
        
        service_name = f"{company.slug}-app"
        
        return {
            "success": True,
            "provider": "aws",
            "service_name": service_name,
            "url": f"https://{service_name}.elasticbeanstalk.com",
            "note": "AWS provisioning requires additional setup"
        }
    
    async def _provision_vercel_service(self, company: Company) -> Dict[str, Any]:
        """Provision service on Vercel."""
        # Vercel API integration
        # Placeholder implementation
        
        return {
            "success": True,
            "provider": "vercel",
            "note": "Vercel provisioning requires Vercel API token"
        }
    
    async def provision_database(
        self,
        company: Company,
        provider: str = "neon"
    ) -> Dict[str, Any]:
        """
        Provision a database for the company.
        
        Args:
            company: Company to provision for
            provider: Provider to use (neon, aws_rds, supabase)
            
        Returns:
            Provisioning result
        """
        logger.info(f"Provisioning database for {company.name} via {provider}")
        
        if provider == "neon":
            return await self._provision_neon_database(company)
        elif provider == "aws_rds":
            return await self._provision_rds_database(company)
        elif provider == "supabase":
            return await self._provision_supabase_database(company)
        else:
            return {"error": f"Unknown provider: {provider}"}
    
    async def _provision_neon_database(self, company: Company) -> Dict[str, Any]:
        """Provision database on Neon."""
        if not settings.NEON_API_KEY:
            return {"error": "Neon API key not configured"}
        
        try:
            # Neon API: https://neon.tech/docs/manage/projects
            
            project_name = f"{company.slug}-db"
            
            response = await self._http_client.post(
                "https://console.neon.tech/api/v2/projects",
                headers={
                    "Authorization": f"Bearer {settings.NEON_API_KEY}",
                    "Accept": "application/json"
                },
                json={
                    "project": {
                        "name": project_name,
                        "region_id": "aws-us-east-1"
                    }
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Update company infrastructure
                company.infrastructure.database_provider = "neon"
                company.infrastructure.database_url = data.get("connection_uris", [{}])[0].get("connection_uri")
                company.infrastructure.database_status = "provisioned"
                
                return {
                    "success": True,
                    "provider": "neon",
                    "project_name": project_name,
                    "connection_string": "postgresql://..."  # Masked
                }
            else:
                return {
                    "success": False,
                    "error": f"Neon API error: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Neon provisioning error: {e}")
            return {"error": str(e)}
    
    async def _provision_rds_database(self, company: Company) -> Dict[str, Any]:
        """Provision RDS database on AWS."""
        # Placeholder for RDS provisioning
        return {
            "success": True,
            "provider": "aws_rds",
            "note": "RDS provisioning requires AWS credentials"
        }
    
    async def _provision_supabase_database(self, company: Company) -> Dict[str, Any]:
        """Provision database on Supabase."""
        # Placeholder for Supabase provisioning
        return {
            "success": True,
            "provider": "supabase",
            "note": "Supabase provisioning requires Supabase API key"
        }
    
    async def provision_email(
        self,
        company: Company,
        provider: str = "sendgrid"
    ) -> Dict[str, Any]:
        """
        Provision email service for the company.
        
        Args:
            company: Company to provision for
            provider: Provider to use (sendgrid, aws_ses)
            
        Returns:
            Provisioning result
        """
        logger.info(f"Provisioning email for {company.name} via {provider}")
        
        if provider == "sendgrid":
            return await self._provision_sendgrid(company)
        elif provider == "aws_ses":
            return await self._provision_aws_ses(company)
        else:
            return {"error": f"Unknown provider: {provider}"}
    
    async def _provision_sendgrid(self, company: Company) -> Dict[str, Any]:
        """Provision SendGrid email service."""
        if not settings.SENDGRID_API_KEY:
            return {"error": "SendGrid API key not configured"}
        
        try:
            # Create subuser for company
            # SendGrid API: https://docs.sendgrid.com/api-reference/subusers-api
            
            subuser_name = f"{company.slug}-{company.id[:8]}"
            
            response = await self._http_client.post(
                "https://api.sendgrid.com/v3/subusers",
                headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
                json={
                    "username": subuser_name,
                    "email": company.settings.notification_email or f"admin@{company.slug}.com",
                    "password": self._generate_password(),  # Generate secure password
                    "ips": []
                }
            )
            
            if response.status_code in [200, 201]:
                # Update company infrastructure
                company.infrastructure.email_provider = "sendgrid"
                company.infrastructure.email_domain = f"{company.slug}.com"
                company.infrastructure.email_status = "provisioned"
                
                return {
                    "success": True,
                    "provider": "sendgrid",
                    "subuser": subuser_name
                }
            else:
                return {
                    "success": False,
                    "error": f"SendGrid API error: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"SendGrid provisioning error: {e}")
            return {"error": str(e)}
    
    async def _provision_aws_ses(self, company: Company) -> Dict[str, Any]:
        """Provision AWS SES email service."""
        # Placeholder for SES provisioning
        return {
            "success": True,
            "provider": "aws_ses",
            "note": "SES provisioning requires AWS credentials"
        }
    
    async def create_github_repo(self, company: Company) -> Dict[str, Any]:
        """
        Create GitHub repository for the company.
        
        Args:
            company: Company to create repo for
            
        Returns:
            Creation result
        """
        logger.info(f"Creating GitHub repo for {company.name}")
        
        if not settings.GITHUB_TOKEN:
            return {"error": "GitHub token not configured"}
        
        try:
            repo_name = company.slug
            org = settings.GITHUB_ORG
            
            if org:
                url = f"https://api.github.com/orgs/{org}/repos"
            else:
                url = "https://api.github.com/user/repos"
            
            response = await self._http_client.post(
                url,
                headers={
                    "Authorization": f"token {settings.GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "name": repo_name,
                    "description": f"{company.name} - Managed by BuizSwarm",
                    "private": True,
                    "auto_init": True,
                    "gitignore_template": "Python"
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Update company infrastructure
                company.infrastructure.github_repo = data.get("full_name")
                company.infrastructure.github_org = org
                company.infrastructure.github_status = "provisioned"
                
                return {
                    "success": True,
                    "repo_url": data.get("html_url"),
                    "clone_url": data.get("clone_url"),
                    "repo_name": data.get("full_name")
                }
            else:
                return {
                    "success": False,
                    "error": f"GitHub API error: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"GitHub repo creation error: {e}")
            return {"error": str(e)}
    
    async def setup_stripe(self, company: Company) -> Dict[str, Any]:
        """
        Setup Stripe account for the company.
        
        Args:
            company: Company to setup Stripe for
            
        Returns:
            Setup result
        """
        logger.info(f"Setting up Stripe for {company.name}")
        
        if not settings.STRIPE_SECRET_KEY:
            return {"error": "Stripe API key not configured"}
        
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Create connected account
            account = stripe.Account.create(
                type="standard",
                country="US",
                email=company.settings.notification_email or f"billing@{company.slug}.com",
                business_type="company",
                company={
                    "name": company.name
                },
                metadata={
                    "buizswarm_company_id": company.id
                }
            )
            
            # Update company infrastructure
            company.infrastructure.stripe_account_id = account.id
            company.infrastructure.stripe_status = "provisioned"
            
            # Create account link for onboarding
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url=f"https://buizswarm.com/stripe/refresh?company={company.id}",
                return_url=f"https://buizswarm.com/stripe/return?company={company.id}",
                type="account_onboarding"
            )
            
            return {
                "success": True,
                "account_id": account.id,
                "onboarding_url": account_link.url
            }
            
        except Exception as e:
            logger.error(f"Stripe setup error: {e}")
            return {"error": str(e)}
    
    def _generate_password(self, length: int = 32) -> str:
        """Generate a secure random password."""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def get_infrastructure_status(self, company: Company) -> Dict[str, Any]:
        """Get infrastructure status for a company."""
        return {
            "web_server": {
                "provider": company.infrastructure.web_server_provider,
                "status": company.infrastructure.web_server_status,
                "url": company.infrastructure.web_server_url
            },
            "database": {
                "provider": company.infrastructure.database_provider,
                "status": company.infrastructure.database_status,
                "url": company.infrastructure.database_url is not None
            },
            "email": {
                "provider": company.infrastructure.email_provider,
                "status": company.infrastructure.email_status,
                "domain": company.infrastructure.email_domain
            },
            "github": {
                "repo": company.infrastructure.github_repo,
                "status": company.infrastructure.github_status
            },
            "stripe": {
                "account_id": company.infrastructure.stripe_account_id,
                "status": company.infrastructure.stripe_status
            }
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        await self._http_client.aclose()


# Global service instance
_infrastructure_service: Optional[InfrastructureService] = None


def get_infrastructure_service() -> InfrastructureService:
    """Get or create global infrastructure service."""
    global _infrastructure_service
    if _infrastructure_service is None:
        _infrastructure_service = InfrastructureService()
    return _infrastructure_service
