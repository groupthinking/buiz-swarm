"""HTTP bridge exposing the local OpenClaw runtime as an MCP-style service."""

from __future__ import annotations

import asyncio
import json
import logging
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import websockets
from fastapi import FastAPI
from pydantic import BaseModel, Field

from .config import settings

logger = logging.getLogger(__name__)
app = FastAPI(title="OpenClaw Bridge", version="1.1.0")

APP_VERSION = "1.1.0"
GATEWAY_PROTOCOL_VERSION = 3
GATEWAY_CLIENT_ID = "gateway-client"
GATEWAY_CLIENT_MODE = "backend"
GATEWAY_CLIENT_DISPLAY_NAME = "BuizSwarm OpenClaw Bridge"
GATEWAY_OPERATOR_SCOPES = [
    "operator.admin",
    "operator.read",
    "operator.write",
    "operator.approvals",
    "operator.pairing",
]
DEFAULT_EXECUTION_TIMEOUT_SECONDS = 20
DEFAULT_GATEWAY_TIMEOUT_MS = 10_000
CHAT_HISTORY_LIMIT = 8
CHAT_POLL_INTERVAL_SECONDS = 1.0

AGENT_METADATA: Dict[str, Dict[str, Any]] = {
    "main": {
        "name": "Clawdbot",
        "description": "Primary multi-purpose agent with full tool access.",
        "emoji": "🦝",
        "capabilities": ["read", "write", "exec", "web_search", "memory", "sessions"],
    },
    "strategist": {
        "name": "Revenue Strategist",
        "description": "Strategic planning and business intelligence.",
        "emoji": "📈",
        "capabilities": ["analysis", "planning", "memory_search", "web_search"],
    },
    "market-intel": {
        "name": "Market Intelligence",
        "description": "Market research and competitive analysis.",
        "emoji": "🔎",
        "capabilities": ["web_search", "web_fetch", "analysis", "reporting"],
    },
    "deal-ops": {
        "name": "Deal Operations",
        "description": "Deal management and operational coordination.",
        "emoji": "🤝",
        "capabilities": ["execution", "coordination", "tracking", "documentation"],
    },
    "growth-finance": {
        "name": "Growth Finance",
        "description": "Growth strategy and financial analysis.",
        "emoji": "💰",
        "capabilities": ["analysis", "forecasting", "optimization", "reporting"],
    },
    "youtube-ops": {
        "name": "YouTube Ops",
        "description": "Content operations and YouTube management.",
        "emoji": "🎬",
        "capabilities": ["content_creation", "scheduling", "analytics", "optimization"],
    },
    "twilio-sms": {
        "name": "SMS Automation",
        "description": "Twilio SMS and communication automation.",
        "emoji": "💬",
        "capabilities": ["sms", "messaging", "automation", "outreach"],
    },
}
AGENT_ORDER = [
    "main",
    "strategist",
    "market-intel",
    "deal-ops",
    "growth-finance",
    "youtube-ops",
    "twilio-sms",
]
MODE_INSTRUCTIONS = {
    "execute": "Execute the request directly and return the concrete result.",
    "analyze": "Analyze the request and return a concise assessment with recommendations.",
    "plan": "Return a concrete step-by-step plan to accomplish the request.",
    "report": "Return a concise operational report with findings, risks, and next actions.",
}


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class GatewayBridgeError(RuntimeError):
    """Raised when the bridge cannot authenticate or talk to OpenClaw."""


class OpenClawGatewayClient:
    """Minimal WebSocket client for the OpenClaw gateway."""

    def __init__(self, url: str, token: Optional[str] = None, password: Optional[str] = None):
        self.url = url
        self.token = token
        self.password = password
        self._ws: Any = None

    async def __aenter__(self) -> "OpenClawGatewayClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def connect(self) -> None:
        self._ws = await websockets.connect(self.url, max_size=25 * 1024 * 1024, open_timeout=DEFAULT_GATEWAY_TIMEOUT_MS / 1000)
        challenge = await self._recv_until_connect_challenge()
        nonce = (challenge.get("payload") or {}).get("nonce")
        if not isinstance(nonce, str) or not nonce.strip():
            raise GatewayBridgeError("gateway connect challenge missing nonce")

        auth: Dict[str, str] = {}
        if self.token:
            auth["token"] = self.token
        if self.password:
            auth["password"] = self.password

        connect_payload = await self._request(
            "connect",
            {
                "minProtocol": GATEWAY_PROTOCOL_VERSION,
                "maxProtocol": GATEWAY_PROTOCOL_VERSION,
                "client": {
                    "id": GATEWAY_CLIENT_ID,
                    "displayName": GATEWAY_CLIENT_DISPLAY_NAME,
                    "version": APP_VERSION,
                    "platform": platform.system().lower(),
                    "mode": GATEWAY_CLIENT_MODE,
                },
                "role": "operator",
                "scopes": GATEWAY_OPERATOR_SCOPES,
                "auth": auth or None,
            },
            timeout_ms=DEFAULT_GATEWAY_TIMEOUT_MS,
        )
        logger.debug("Connected to OpenClaw gateway: %s", connect_payload)

    async def close(self) -> None:
        if self._ws is None:
            return
        try:
            await self._ws.close()
        finally:
            self._ws = None

    async def call(self, method: str, params: Optional[Dict[str, Any]] = None, *, timeout_ms: int = DEFAULT_GATEWAY_TIMEOUT_MS) -> Dict[str, Any]:
        return await self._request(method, params or {}, timeout_ms=timeout_ms)

    async def _recv_until_connect_challenge(self) -> Dict[str, Any]:
        deadline = asyncio.get_running_loop().time() + (DEFAULT_GATEWAY_TIMEOUT_MS / 1000)
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise GatewayBridgeError("gateway connect challenge timeout")
            message = await self._recv_json(int(remaining * 1000))
            if message.get("type") == "event" and message.get("event") == "connect.challenge":
                return message

    async def _request(self, method: str, params: Dict[str, Any], *, timeout_ms: int) -> Dict[str, Any]:
        if self._ws is None:
            raise GatewayBridgeError("gateway not connected")
        request_id = str(uuid.uuid4())
        frame = {
            "type": "req",
            "id": request_id,
            "method": method,
            "params": params,
        }
        await self._ws.send(json.dumps(frame))
        deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise GatewayBridgeError(f"gateway timeout waiting for {method}")
            message = await self._recv_json(int(remaining * 1000))
            if message.get("type") == "event":
                continue
            if message.get("type") != "res" or message.get("id") != request_id:
                continue
            if message.get("ok") is True:
                payload = message.get("payload")
                return payload if isinstance(payload, dict) else {"result": payload}
            error = message.get("error") or {}
            error_message = error.get("message") if isinstance(error, dict) else str(error)
            raise GatewayBridgeError(error_message or f"gateway {method} call failed")


    async def run_agent(self, params: Dict[str, Any], *, timeout_seconds: int) -> Dict[str, Any]:
        if self._ws is None:
            raise GatewayBridgeError("gateway not connected")
        request_id = str(uuid.uuid4())
        frame = {
            "type": "req",
            "id": request_id,
            "method": "agent",
            "params": params,
        }
        await self._ws.send(json.dumps(frame))

        deadline = asyncio.get_running_loop().time() + max(5, timeout_seconds + 10)
        accepted: Optional[Dict[str, Any]] = None
        final: Optional[Dict[str, Any]] = None
        assistant_text = ""
        run_id: Optional[str] = None
        session_key = str(params.get("sessionKey") or "")

        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                return {
                    "accepted": accepted,
                    "final": final,
                    "assistant_text": assistant_text.strip(),
                }

            message = await self._recv_json(int(min(remaining * 1000, DEFAULT_GATEWAY_TIMEOUT_MS)))
            if message.get("type") == "event":
                assistant_text = _extract_text_from_gateway_event(assistant_text, message, run_id, session_key)
                continue
            if message.get("type") != "res" or message.get("id") != request_id:
                continue
            if message.get("ok") is not True:
                error = message.get("error") or {}
                error_message = error.get("message") if isinstance(error, dict) else str(error)
                raise GatewayBridgeError(error_message or "gateway agent call failed")

            payload = message.get("payload")
            payload_dict = payload if isinstance(payload, dict) else {"result": payload}
            status = str(payload_dict.get("status") or "")
            if status == "accepted" and accepted is None:
                accepted = payload_dict
                run_id = str(payload_dict.get("runId") or run_id or "") or None
                continue

            final = payload_dict
            run_id = str(payload_dict.get("runId") or run_id or "") or None
            assistant_text = _extract_text_from_agent_result(payload_dict, assistant_text)
            return {
                "accepted": accepted,
                "final": final,
                "assistant_text": assistant_text.strip(),
            }

    async def _recv_json(self, timeout_ms: int) -> Dict[str, Any]:
        if self._ws is None:
            raise GatewayBridgeError("gateway connection is closed")
        try:
            raw = await asyncio.wait_for(self._ws.recv(), timeout_ms / 1000)
        except asyncio.TimeoutError as exc:
            raise GatewayBridgeError("gateway receive timeout") from exc
        except websockets.ConnectionClosed as exc:
            raise GatewayBridgeError(f"gateway closed ({exc.code}): {exc.reason}") from exc
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _config_path() -> Path:
    return Path(settings.OPENCLAW_HOME) / "openclaw.json"


def _load_config() -> Dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to load OpenClaw config from %s: %s", path, exc)
        return {}


def _resolve_gateway_ws_url(config: Dict[str, Any]) -> str:
    raw = (settings.OPENCLAW_GATEWAY_URL or "").strip()
    if not raw:
        port = config.get("gateway", {}).get("port", 18789)
        raw = f"http://127.0.0.1:{port}"
    parsed = urlparse(raw if "://" in raw else f"http://{raw}")
    scheme = "wss" if parsed.scheme in {"https", "wss"} else "ws"
    netloc = parsed.netloc or parsed.path
    path = parsed.path if parsed.netloc else ""
    if not netloc:
        raise GatewayBridgeError("OpenClaw gateway URL is not configured")
    return urlunparse((scheme, netloc, path or "", "", "", ""))


def _resolve_gateway_auth(config: Dict[str, Any]) -> Dict[str, Optional[str]]:
    env_token = (settings.OPENCLAW_GATEWAY_TOKEN or "").strip() or None
    config_auth = config.get("gateway", {}).get("auth", {})
    config_token = str(config_auth.get("token", "")).strip() or None
    config_password = str(config_auth.get("password", "")).strip() or None

    if env_token:
        return {"token": env_token, "password": None, "source": "env"}
    if config_token:
        return {"token": config_token, "password": None, "source": "config"}
    if config_password:
        return {"token": None, "password": config_password, "source": "config"}

    raise GatewayBridgeError("OpenClaw gateway auth is not configured. Set OPENCLAW_GATEWAY_TOKEN or gateway.auth.token.")


def _configured_agents(config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    config = config or _load_config()
    configured = config.get("agents", {}).get("list", [])
    default_id = config.get("agents", {}).get("default", "main")
    configured_by_id = {
        entry.get("id"): entry
        for entry in configured
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }

    agent_ids = [agent_id for agent_id in AGENT_ORDER if agent_id in configured_by_id] or AGENT_ORDER
    agents: List[Dict[str, Any]] = []
    for agent_id in agent_ids:
        entry = configured_by_id.get(agent_id, {})
        identity = entry.get("identity") or {}
        metadata = AGENT_METADATA.get(agent_id, {})
        agents.append(
            {
                "id": agent_id,
                "name": identity.get("name") or entry.get("name") or metadata.get("name") or agent_id,
                "description": metadata.get("description", "OpenClaw specialist."),
                "emoji": identity.get("emoji") or metadata.get("emoji", ""),
                "capabilities": metadata.get("capabilities", []),
                "default": agent_id == default_id,
            }
        )
    return agents


def _build_tools() -> List[Dict[str, Any]]:
    tools: List[Dict[str, Any]] = []
    for agent in _configured_agents():
        tools.append(
            {
                "name": f"openclaw_{agent['id']}",
                "description": f"Invoke {agent['name']} {agent['emoji']}. {agent['description']} Capabilities: {', '.join(agent['capabilities'])}",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task description for the agent to execute."},
                        "context": {"type": "object", "description": "Optional structured context to include."},
                        "mode": {
                            "type": "string",
                            "enum": ["execute", "analyze", "plan", "report"],
                            "description": "How the agent should respond.",
                        },
                        "timeout_seconds": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 300,
                            "description": "How long to wait for the agent reply before returning timeout.",
                        },
                    },
                    "required": ["task"],
                },
            }
        )

    tools.extend(
        [
            {
                "name": "openclaw_list_agents",
                "description": "List all available OpenClaw agents with their capabilities.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "openclaw_agent_info",
                "description": "Get detailed information about a specific OpenClaw agent.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "Agent ID such as main or strategist."}
                    },
                    "required": ["agent_id"],
                },
            },
            {
                "name": "openclaw_execute_workflow",
                "description": "Execute a multi-agent workflow, either sequentially or in parallel when there are no dependencies.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "agent": {"type": "string"},
                                    "task": {"type": "string"},
                                    "context": {"type": "object"},
                                    "mode": {"type": "string", "enum": ["execute", "analyze", "plan", "report"]},
                                    "depends_on": {"type": "array", "items": {"type": "integer"}},
                                },
                                "required": ["agent", "task"],
                            },
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["sequential", "parallel"],
                            "description": "Parallel mode is used only when no step dependencies are declared.",
                        },
                        "timeout_seconds": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 300,
                            "description": "How long to wait for each workflow step reply.",
                        },
                    },
                    "required": ["workflow"],
                },
            },
            {
                "name": "openclaw_system_status",
                "description": "Get OpenClaw gateway connectivity and runtime summary.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]
    )
    return tools


def _session_key_for_agent(agent_id: str) -> str:
    return f"agent:{agent_id}:buizswarm-bridge"


def _render_task(task: str, context: Dict[str, Any], mode: str) -> str:
    sections = [task.strip()]
    instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["execute"])
    sections.append(instruction)
    if context:
        sections.append("Context:\n" + json.dumps(context, indent=2, sort_keys=True, default=str))
    return "\n\n".join(section for section in sections if section)


def _extract_text_from_gateway_event(current_text: str, message: Dict[str, Any], run_id: Optional[str], session_key: str) -> str:
    if message.get("type") != "event":
        return current_text

    payload = message.get("payload") or {}
    payload_session_key = str(payload.get("sessionKey") or "")
    if session_key and payload_session_key and payload_session_key != session_key:
        return current_text

    payload_run_id = str(payload.get("runId") or "")
    if run_id and payload_run_id and payload_run_id != run_id:
        return current_text

    if message.get("event") == "agent" and payload.get("stream") == "assistant":
        data = payload.get("data") or {}
        text = str(data.get("text") or "").strip()
        delta = str(data.get("delta") or "")
        if text:
            return text
        if delta:
            return f"{current_text}{delta}".strip()

    if message.get("event") == "chat":
        chat_message = payload.get("message")
        if isinstance(chat_message, dict):
            text = _extract_text_from_message(chat_message)
            if text:
                return text

    return current_text


def _extract_text_from_agent_result(result: Dict[str, Any], fallback: str = "") -> str:
    payloads = ((result.get("result") or {}).get("payloads") or [])
    texts: List[str] = []
    for payload in payloads:
        if isinstance(payload, dict):
            text = str(payload.get("text") or "").strip()
            if text:
                texts.append(text)
    if texts:
        return "\n".join(texts).strip()
    return fallback.strip()


def _extract_text_from_message(message: Dict[str, Any]) -> str:
    parts: List[str] = []
    for item in message.get("content", []) or []:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            text = item["text"].strip()
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def _find_reply_since(messages: List[Dict[str, Any]], since_ms: int) -> Optional[Dict[str, Any]]:
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue
        timestamp = int(message.get("timestamp") or 0)
        if timestamp and timestamp < since_ms:
            continue
        text = _extract_text_from_message(message)
        if not text:
            continue
        return {
            "text": text,
            "timestamp": timestamp,
            "provider": message.get("provider"),
            "model": message.get("model"),
            "stop_reason": message.get("stopReason"),
        }
    return None


async def _poll_for_reply(gateway: OpenClawGatewayClient, session_key: str, since_ms: int, timeout_seconds: int) -> Optional[Dict[str, Any]]:
    deadline = asyncio.get_running_loop().time() + max(1, timeout_seconds)
    while asyncio.get_running_loop().time() < deadline:
        history = await gateway.call(
            "chat.history",
            {"sessionKey": session_key, "limit": CHAT_HISTORY_LIMIT},
            timeout_ms=DEFAULT_GATEWAY_TIMEOUT_MS,
        )
        reply = _find_reply_since(history.get("messages", []), since_ms)
        if reply:
            return reply
        await asyncio.sleep(CHAT_POLL_INTERVAL_SECONDS)
    return None


async def _gateway_status(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = config or _load_config()
    try:
        auth = _resolve_gateway_auth(config)
        async with OpenClawGatewayClient(
            _resolve_gateway_ws_url(config),
            token=auth.get("token"),
            password=auth.get("password"),
        ) as gateway:
            health = await gateway.call("health", {}, timeout_ms=DEFAULT_GATEWAY_TIMEOUT_MS)
        return {
            "reachable": True,
            "auth_source": auth.get("source"),
            "default_agent_id": health.get("defaultAgentId"),
            "agent_count": len(health.get("agents", [])),
            "channels": health.get("channelOrder", []),
        }
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}


async def _invoke_agent(agent: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    task = str(args.get("task", "")).strip()
    if not task:
        raise ValueError("Missing required parameter: task")

    config = _load_config()
    auth = _resolve_gateway_auth(config)
    mode = str(args.get("mode", "execute") or "execute")
    timeout_seconds = int(args.get("timeout_seconds") or DEFAULT_EXECUTION_TIMEOUT_SECONDS)
    timeout_seconds = max(1, min(timeout_seconds, 300))
    session_key = _session_key_for_agent(agent["id"])
    idempotency_key = f"buizswarm-{agent['id']}-{uuid.uuid4()}"
    prompt = _render_task(task, args.get("context") or {}, mode)

    async with OpenClawGatewayClient(
        _resolve_gateway_ws_url(config),
        token=auth.get("token"),
        password=auth.get("password"),
    ) as gateway:
        run = await gateway.run_agent(
            {
                "message": prompt,
                "agentId": agent["id"],
                "sessionKey": session_key,
                "timeout": timeout_seconds,
                "deliver": False,
                "idempotencyKey": idempotency_key,
            },
            timeout_seconds=timeout_seconds,
        )

    accepted = run.get("accepted") or {}
    final = run.get("final") or {}
    reply_text = _extract_text_from_agent_result(final, run.get("assistant_text") or "")
    run_id = str((final.get("runId") or accepted.get("runId") or idempotency_key))

    if str(final.get("status") or "") == "ok" and reply_text:
        agent_meta = ((final.get("result") or {}).get("meta") or {}).get("agentMeta") or {}
        return {
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "status": "ok",
            "mode": mode,
            "run_id": run_id,
            "session_key": session_key,
            "reply": reply_text,
            "response": {
                "text": reply_text,
                "provider": agent_meta.get("provider"),
                "model": agent_meta.get("model"),
                "stop_reason": final.get("summary"),
            },
            "accepted": accepted,
            "final": final,
            "completed_at": _utc_now(),
        }

    final_status = str(final.get("status") or "")
    if final_status and final_status != "accepted":
        error_message = str(final.get("summary") or run.get("assistant_text") or "agent execution failed")
        return {
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "status": final_status,
            "mode": mode,
            "run_id": run_id,
            "session_key": session_key,
            "accepted": accepted,
            "final": final,
            "error": error_message,
            "completed_at": _utc_now(),
        }

    return {
        "agent_id": agent["id"],
        "agent_name": agent["name"],
        "status": "timeout",
        "mode": mode,
        "run_id": run_id,
        "session_key": session_key,
        "accepted": accepted,
        "timeout_seconds": timeout_seconds,
        "completed_at": _utc_now(),
    }


async def _execute_workflow(args: Dict[str, Any], agents: List[Dict[str, Any]]) -> Dict[str, Any]:
    workflow = args.get("workflow") or []
    if not workflow:
        raise ValueError("Missing required parameter: workflow")

    workflow_id = f"workflow-{uuid.uuid4()}"
    mode = str(args.get("mode", "sequential") or "sequential")
    timeout_seconds = int(args.get("timeout_seconds") or DEFAULT_EXECUTION_TIMEOUT_SECONDS)
    agent_map = {agent["id"]: agent for agent in agents}
    has_dependencies = any(step.get("depends_on") for step in workflow if isinstance(step, dict))
    effective_mode = "sequential" if has_dependencies else mode

    async def run_step(index: int, step: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = step.get("agent")
        agent = agent_map.get(agent_id)
        if not agent:
            return {"step": index, "status": "error", "error": f"Agent {agent_id} not found"}
        try:
            result = await _invoke_agent(
                agent,
                {
                    "task": step.get("task", ""),
                    "context": step.get("context", {}),
                    "mode": step.get("mode", "execute"),
                    "timeout_seconds": timeout_seconds,
                },
            )
            return {"step": index, **result}
        except Exception as exc:  # pragma: no cover - defensive
            return {"step": index, "status": "error", "agent_id": agent_id, "error": str(exc)}

    if effective_mode == "parallel":
        results = await asyncio.gather(*(run_step(index, step) for index, step in enumerate(workflow)))
    else:
        results = []
        for index, step in enumerate(workflow):
            results.append(await run_step(index, step))

    return {
        "workflow_id": workflow_id,
        "requested_mode": mode,
        "effective_mode": effective_mode,
        "steps": len(workflow),
        "results": results,
        "initiated_at": _utc_now(),
    }


async def _handle_tool_call(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    config = _load_config()
    agents = _configured_agents(config)
    agent_map = {agent["id"]: agent for agent in agents}

    if name.startswith("openclaw_") and name not in {
        "openclaw_list_agents",
        "openclaw_agent_info",
        "openclaw_execute_workflow",
        "openclaw_system_status",
    }:
        agent_id = name.removeprefix("openclaw_")
        agent = agent_map.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        return await _invoke_agent(agent, args)

    if name == "openclaw_list_agents":
        return {"agents": agents}

    if name == "openclaw_agent_info":
        agent_id = str(args.get("agent_id", "")).strip()
        agent = agent_map.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        return {
            **agent,
            "default_model": config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "unknown"),
            "session_key": _session_key_for_agent(agent_id),
        }

    if name == "openclaw_execute_workflow":
        return await _execute_workflow(args, agents)

    if name == "openclaw_system_status":
        gateway_status = await _gateway_status(config)
        return {
            "status": "operational" if _config_path().exists() and gateway_status.get("reachable") else "degraded",
            "agents": len(agents),
            "default_agent_id": next((agent["id"] for agent in agents if agent.get("default")), None),
            "config_path": str(_config_path()),
            "config_present": _config_path().exists(),
            "memory_backend": config.get("memory", {}).get("backend", "builtin"),
            "gateway_url": settings.OPENCLAW_GATEWAY_URL,
            "gateway_ws_url": _resolve_gateway_ws_url(config),
            "gateway_status": gateway_status,
            "timestamp": _utc_now(),
        }

    raise ValueError(f"Unknown tool: {name}")


@app.get("/health")
async def health() -> Dict[str, Any]:
    config = _load_config()
    gateway_status = await _gateway_status(config)
    return {
        "status": "ok" if gateway_status.get("reachable") else "degraded",
        "config_present": _config_path().exists(),
        "gateway_url": settings.OPENCLAW_GATEWAY_URL,
        "gateway_status": gateway_status,
        "timestamp": _utc_now(),
    }


@app.post("/mcp/initialize")
async def initialize(_: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}, "resources": {}},
        "serverInfo": {"name": "OpenClaw Bridge", "version": APP_VERSION},
    }


@app.post("/mcp/tools/list")
async def list_tools(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"tools": _build_tools()}


@app.post("/mcp/resources/list")
async def list_resources(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"resources": []}


@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest) -> Dict[str, Any]:
    try:
        result = await _handle_tool_call(request.name, request.arguments)
        return {"content": result}
    except Exception as exc:
        logger.error("OpenClaw bridge tool call failed for %s: %s", request.name, exc)
        return {"isError": True, "content": str(exc)}
