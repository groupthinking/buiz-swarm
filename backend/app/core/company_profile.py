"""
Company profile loader for ProfitMax-style runtime overlays.

Loads the vendored ProfitMax manifest and turns curated role files into
prompt overlays that can be attached to BuizSwarm agents at runtime.
"""
import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agents.base_agent import AgentConfig
from ..config import settings

logger = logging.getLogger(__name__)


def _strip_frontmatter(text: str) -> str:
    """Remove simple markdown frontmatter if present."""
    if not text.startswith("---\n"):
        return text

    marker = "\n---\n"
    end = text.find(marker, 4)
    if end == -1:
        return text
    return text[end + len(marker):]


def _markdown_excerpt(text: str, max_chars: int = 2200) -> str:
    """
    Extract a concise, high-signal excerpt from a markdown role file.

    This avoids dumping full role libraries into every agent prompt while still
    carrying over the core mission and working rules.
    """
    body = _strip_frontmatter(text).strip()
    if not body:
        return ""

    preferred_headings = (
        "core mission",
        "critical rules",
        "workflow process",
        "principles",
        "decision logic",
        "quick-start",
    )

    sections: List[str] = []
    current: List[str] = []
    for line in body.splitlines():
        if line.startswith("#") and current:
            sections.append("\n".join(current).strip())
            current = []
        current.append(line)
    if current:
        sections.append("\n".join(current).strip())

    selected = [
        section for section in sections
        if any(heading in section.lower() for heading in preferred_headings)
    ]
    if not selected:
        selected = sections[:2]

    excerpt = "\n\n".join(selected).strip()
    excerpt = re.sub(r"\n{3,}", "\n\n", excerpt)
    return excerpt[:max_chars].strip()


def _workflow_prompt_list(items: List[str], heading: str) -> str:
    """Render a markdown bullet list for workflow instructions."""
    if not items:
        return ""
    rendered = "\n".join(f"- {item}" for item in items)
    return f"{heading}\n{rendered}"


class CompanyProfileManager:
    """Loads and applies the configured company profile manifest."""

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        self.root = self.manifest_path.parent
        self._manifest_cache: Optional[Dict[str, Any]] = None

    def load_manifest(self) -> Dict[str, Any]:
        """Load the manifest from disk if present."""
        if self._manifest_cache is not None:
            return self._manifest_cache

        if not self.manifest_path.exists():
            logger.warning("Company profile manifest not found: %s", self.manifest_path)
            self._manifest_cache = {}
            return self._manifest_cache

        with self.manifest_path.open("r", encoding="utf-8") as handle:
            self._manifest_cache = json.load(handle)
        return self._manifest_cache

    def is_enabled(self) -> bool:
        """Return whether a usable profile manifest is available."""
        manifest = self.load_manifest()
        return bool(manifest)

    def describe(self) -> Dict[str, Any]:
        """Return a summary of the loaded profile."""
        manifest = self.load_manifest()
        roles = manifest.get("roles", {})
        return {
            "enabled": bool(manifest),
            "profile": manifest.get("name", settings.DEFAULT_COMPANY_PROFILE),
            "goal": manifest.get("goal"),
            "manifest_path": str(self.manifest_path),
            "role_types": sorted(roles.keys()),
            "workflow_ids": sorted(manifest.get("workflows", {}).keys()),
            "operator_skills": self.list_operator_skills(),
        }

    def _resolve_relpath(self, relpath: str) -> Path:
        """Resolve a path relative to the manifest root."""
        return (self.root / relpath).resolve()

    def _get_agent_role_paths(self, agent_type: str) -> List[str]:
        """Get role-pack relative paths for an agent type."""
        manifest = self.load_manifest()
        role_data = manifest.get("roles", {}).get(agent_type, {})
        return list(role_data.get("role_pack", []))

    def list_operator_skills(self) -> Dict[str, Dict[str, Any]]:
        """Return the curated operator skills from the manifest."""
        manifest = self.load_manifest()
        return dict(manifest.get("operator_skills", {}))

    def list_workflows(self) -> List[Dict[str, Any]]:
        """Return summarized workflow definitions."""
        manifest = self.load_manifest()
        workflows = manifest.get("workflows", {})
        return [
            {
                "workflow_id": workflow_id,
                "name": workflow.get("name", workflow_id),
                "agent_type": workflow.get("agent_type"),
                "task_type": workflow.get("task_type"),
                "openclaw_agent_id": workflow.get("openclaw_agent_id"),
                "openclaw_mode": workflow.get("openclaw_mode", "execute"),
                "summary": workflow.get("summary", ""),
                "inputs": workflow.get("inputs", []),
                "operator_skills": workflow.get("operator_skills", []),
                "output_requirements": workflow.get("output_requirements", []),
            }
            for workflow_id, workflow in workflows.items()
        ]

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Return a workflow definition by ID."""
        manifest = self.load_manifest()
        return dict(manifest.get("workflows", {}).get(workflow_id, {}))

    def get_agent_role_sources(self, agent_type: str) -> List[str]:
        """Return the resolved role source paths for an agent type."""
        return [
            str(self._resolve_relpath(relpath))
            for relpath in self._get_agent_role_paths(agent_type)
        ]

    def build_agent_overlay(
        self,
        agent_type: str,
        company_name: Optional[str] = None,
        company_goal: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a runtime prompt overlay for a specific agent type."""
        manifest = self.load_manifest()
        if not manifest:
            return {"profile": None, "sources": [], "prompt": ""}

        profile_name = manifest.get("name", settings.DEFAULT_COMPANY_PROFILE)
        resolved_sources: List[str] = []
        excerpts: List[str] = []
        for relpath in self._get_agent_role_paths(agent_type):
            source_path = self._resolve_relpath(relpath)
            if not source_path.exists():
                continue
            resolved_sources.append(str(source_path))
            text = source_path.read_text(encoding="utf-8")
            excerpt = _markdown_excerpt(text)
            if excerpt:
                excerpts.append(f"Source: {relpath}\n{excerpt}")

        manifest_goal = company_goal or manifest.get("goal", "")
        control_plane = manifest.get("control_plane", {}).get("runtime", "openclaw")
        app_name = manifest.get("execution", {}).get("app", "buiz-swarm")

        lines = [
            f"You are operating inside the {profile_name} company profile.",
            f"Control plane: {control_plane}.",
            f"Execution app: {app_name}.",
        ]
        if company_name:
            lines.append(f"Company name: {company_name}.")
        if manifest_goal:
            lines.append(f"Primary goal: {manifest_goal}")
        if resolved_sources:
            lines.append("Apply the following role overlays when making decisions and executing work:")
            lines.extend(excerpts)

        return {
            "profile": profile_name,
            "sources": resolved_sources,
            "prompt": "\n\n".join(lines).strip(),
        }

    def build_workflow_execution(
        self,
        workflow_id: str,
        company_name: Optional[str] = None,
        company_goal: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build the execution brief for a revenue workflow."""
        manifest = self.load_manifest()
        workflow = manifest.get("workflows", {}).get(workflow_id)
        if not workflow:
            return {}

        operator_skills = self.list_operator_skills()
        skill_ids = workflow.get("operator_skills", [])
        selected_skills = {
            skill_id: operator_skills.get(skill_id, {})
            for skill_id in skill_ids
        }
        input_payload = inputs or {}

        lines = [
            f"Execute the ProfitMax workflow `{workflow_id}`.",
            f"Workflow: {workflow.get('name', workflow_id)}.",
            f"Summary: {workflow.get('summary', '')}",
        ]
        if company_name:
            lines.append(f"Company: {company_name}.")
        if company_goal or manifest.get("goal"):
            lines.append(f"Primary goal: {company_goal or manifest.get('goal')}")
        lines.append(f"Assigned agent type: {workflow.get('agent_type')}.")
        lines.append(f"Expected task type: {workflow.get('task_type')}.")

        skill_lines = [
            f"- {skill_id}: {skill_data.get('purpose', '')}"
            for skill_id, skill_data in selected_skills.items()
        ]
        if skill_lines:
            lines.append("Operator skill stack to lean on when extra research or execution is needed:")
            lines.extend(skill_lines)

        if input_payload:
            lines.append("Workflow inputs:")
            lines.append(json.dumps(input_payload, indent=2, sort_keys=True))

        instruction_block = _workflow_prompt_list(
            workflow.get("execution_prompt", []),
            "Execution rules:",
        )
        if instruction_block:
            lines.append(instruction_block)

        output_block = _workflow_prompt_list(
            workflow.get("output_requirements", []),
            "Required output:",
        )
        if output_block:
            lines.append(output_block)

        lines.append(
            "Respond in structured JSON when possible. If exact JSON is not possible, keep the response tightly structured."
        )

        return {
            "workflow_id": workflow_id,
            "name": workflow.get("name", workflow_id),
            "agent_type": workflow.get("agent_type"),
            "task_type": workflow.get("task_type"),
            "openclaw_agent_id": workflow.get("openclaw_agent_id"),
            "openclaw_mode": workflow.get("openclaw_mode", "execute"),
            "summary": workflow.get("summary", ""),
            "operator_skills": selected_skills,
            "prompt": "\n\n".join(line for line in lines if line).strip(),
        }

    def apply_to_agent_config(
        self,
        config: AgentConfig,
        agent_type: str,
        company_name: Optional[str] = None,
        company_goal: Optional[str] = None,
    ) -> AgentConfig:
        """Return an agent config with the company profile overlay applied."""
        overlay = self.build_agent_overlay(
            agent_type=agent_type,
            company_name=company_name,
            company_goal=company_goal,
        )
        merged = config.model_copy(deep=True)
        if overlay["prompt"]:
            merged.system_prompt = (
                f"{merged.system_prompt.strip()}\n\n"
                f"---\n"
                f"{overlay['prompt']}"
            )
        merged.metadata = {
            **merged.metadata,
            "profile": overlay["profile"],
            "profile_sources": overlay["sources"],
            "profile_goal": company_goal or self.load_manifest().get("goal"),
        }
        return merged


@lru_cache()
def get_company_profile_manager() -> CompanyProfileManager:
    """Return the cached company profile manager."""
    return CompanyProfileManager(settings.COMPANY_PROFILE_MANIFEST)
