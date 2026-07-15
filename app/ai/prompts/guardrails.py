import jsonschema
from typing import Any

class PromptGuardrailException(Exception):
    pass

class PromptGuardrails:
    MAX_PROMPT_LENGTH = 8000

    @staticmethod
    def validate_input(input_data: dict[str, Any], schema: dict[str, Any]) -> None:
        if not schema or not schema.get("properties"):
            return
        try:
            jsonschema.validate(instance=input_data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            raise PromptGuardrailException(f"Missing or invalid variable: {e.message}")

    @staticmethod
    def validate_rendered_prompt(rendered_prompt: str) -> None:
        if len(rendered_prompt) > PromptGuardrails.MAX_PROMPT_LENGTH:
            raise PromptGuardrailException(f"Rendered prompt exceeds maximum allowed length of {PromptGuardrails.MAX_PROMPT_LENGTH}")
        
        # Basic heuristic injection check (e.g., trying to override system instructions)
        lower_prompt = rendered_prompt.lower()
        injection_keywords = [
            "ignore previous instructions", 
            "forget all previous", 
            "system prompt override",
            "reveal system prompt",
            "forget your instructions",
            "you are chatgpt now"
        ]
        for kw in injection_keywords:
            if kw in lower_prompt:
                raise PromptGuardrailException("Potential prompt injection detected in rendered output.")
