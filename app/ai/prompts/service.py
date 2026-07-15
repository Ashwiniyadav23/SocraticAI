import os
import yaml
from jinja2 import Template
from typing import Any
from .guardrails import PromptGuardrails
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.database import db
from app.models import Prompt, PromptVersion, PromptEvaluationLog

class PromptNotFoundError(Exception):
    pass

class PromptService:
    _cache: dict[str, dict[str, Any]] = {}
    _registry_dir: str = os.path.join(os.path.dirname(__file__), "registry")

    @classmethod
    def load_prompt_yaml(cls, name: str) -> dict[str, Any]:
        if name in cls._cache:
            return cls._cache[name]

        file_path = os.path.join(cls._registry_dir, f"{name}.yaml")
        if not os.path.exists(file_path):
            raise PromptNotFoundError(f"Prompt '{name}' not found in registry.")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        cls._cache[name] = data
        return data

    @classmethod
    async def load_prompt(cls, name: str) -> dict[str, Any]:
        """Loads prompt from DB if an active version exists, otherwise falls back to YAML."""
        if not db.session_maker:
            return cls.load_prompt_yaml(name)
            
        async with db.session_maker() as session:
            stmt = select(PromptVersion).where(
                PromptVersion.prompt_name == name,
                PromptVersion.is_active == True
            )
            result = await session.execute(stmt)
            db_version = result.scalars().first()
            
            if db_version:
                return {
                    "name": db_version.prompt_name,
                    "version": db_version.version,
                    "input_schema": db_version.input_schema,
                    "template": db_version.template_text,
                    "source": "db"
                }
                
        # Fallback to YAML
        yaml_data = cls.load_prompt_yaml(name)
        yaml_data["source"] = "yaml"
        return yaml_data

    @classmethod
    async def render(cls, name: str, state: dict[str, Any]) -> tuple[str, str]:
        """Returns the rendered string AND the version used, for telemetry logging."""
        data = await cls.load_prompt(name)
        schema = data.get("input_schema", {})
        version = data.get("version", "unknown")
        
        # 1. Validate variables
        PromptGuardrails.validate_input(state, schema)
        
        # 2. Render Template
        template_str = data.get("template", "")
        template = Template(template_str)
        rendered = template.render(**state).strip()
        
        # 3. Output Guardrails
        PromptGuardrails.validate_rendered_prompt(rendered)
        
        return rendered, version

    @classmethod
    async def log_evaluation(
        cls, 
        prompt_name: str, 
        version: str, 
        tokens: int, 
        cost: float, 
        latency_ms: int, 
        success: bool, 
        failure_reason: str | None = None
    ):
        """Logs prompt execution metrics to the database."""
        if not db.session_maker:
            return
            
        async with db.session_maker() as session:
            # Ensure the prompt exists in the DB to avoid Foreign Key violations
            prompt_stmt = insert(Prompt).values(
                name=prompt_name,
                description="Auto-registered from YAML fallback"
            ).on_conflict_do_nothing()
            await session.execute(prompt_stmt)
            
            log_entry = PromptEvaluationLog(
                prompt_id=prompt_name,
                version=version,
                tokens_used=tokens,
                cost=cost,
                latency_ms=latency_ms,
                success=success,
                failure_reason=failure_reason
            )
            session.add(log_entry)
            await session.commit()
