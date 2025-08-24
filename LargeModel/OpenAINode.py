import json
import base64
from openai import OpenAI, OpenAIError

# Decode base64 defaults
_default_base_url_b64 = "aHR0cDovLzQ3Ljk5LjE0My45ODoxMTQzNC9uMQ=="
_default_key_b64 = "c21lbGwtMTIzNDU2"
default_base_url = base64.b64decode(_default_base_url_b64).decode()
default_key = base64.b64decode(_default_key_b64).decode()

class OpenAINode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "base_url": ("STRING", {"multiline": False, "default": default_base_url}),
                "api_key": ("STRING", {"multiline": False, "default": default_key}),
                "model": ("STRING", {"default": ""}),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True}),
            },
            "optional": {
                "params": ("OPENAI_PARAMS"),
                "history": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("response", "history")
    FUNCTION = "execute"
    CATEGORY = "🌱SmellCommon/LargeModel/OpenAI"
    OUTPUT_NODE = True
    IS_CHANGED = True

    def _load_history(self, history_str):
        if not history_str:
            return []
        try:
            data = json.loads(history_str)
            if isinstance(data, list):
                # filter only valid message dicts
                return [m for m in data if isinstance(m, dict) and "role" in m and "content" in m]
        except Exception:
            pass
        return []

    def _ensure_system(self, messages, system_prompt):
        if not system_prompt:
            return messages
        # only add system if not already present
        for m in messages:
            if m.get("role") == "system":
                return messages
        return [{"role": "system", "content": system_prompt}] + messages

    def execute(self, base_url, api_key, model, system_prompt, user_prompt, params=None, history=None):
        # Load existing history
        messages = self._load_history(history)
        # Ensure system message present (once)
        messages = self._ensure_system(messages, system_prompt)
        # Append current user message
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        client = OpenAI(api_key=api_key, base_url=base_url)

        call_args = {
            "model": model,
            "messages": messages,
        }
        if params:
            # Only include safe known keys
            allowed = {
                "temperature",
                "max_tokens",
                "top_p",
                "frequency_penalty",
                "presence_penalty",
                "stop",
                "n",
                "logit_bias",
                "user",
            }
            for k, v in params.items():
                if k in allowed:
                    call_args[k] = v

        try:
            resp = client.chat.completions.create(**call_args)
        except OpenAIError as e:
            raise Exception(f"OpenAI API error: {e}")

        choice = resp.choices[0] if resp.choices else None
        content = ""
        if choice and getattr(choice, "message", None):
            content = choice.message.content or ""
        if content:
            messages.append({"role": "assistant", "content": content})

        # Return assistant response and updated history JSON
        return (content, json.dumps(messages, ensure_ascii=False),)


class OpenAIParamNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "enable": ("BOOLEAN", {"default": True}),
                "enable_temperature": ("BOOLEAN", {"default": True}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0}),
                "enable_max_tokens": ("BOOLEAN", {"default": True}),
                "max_tokens": ("INT", {"default": 256, "min": 1}),
                "enable_top_p": ("BOOLEAN", {"default": True}),
                "top_p": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
                "enable_frequency_penalty": ("BOOLEAN", {"default": True}),
                "frequency_penalty": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 2.0}),
                "enable_presence_penalty": ("BOOLEAN", {"default": True}),
                "presence_penalty": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 2.0}),
            }
        }

    RETURN_TYPES = ("OPENAI_PARAMS",)
    RETURN_NAMES = ("params",)
    FUNCTION = "build_params"
    CATEGORY = "🌱SmellCommon/LargeModel/OpenAI"

    def build_params(
        self,
        enable,
        enable_temperature, temperature,
        enable_max_tokens, max_tokens,
        enable_top_p, top_p,
        enable_frequency_penalty, frequency_penalty,
        enable_presence_penalty, presence_penalty
    ):
        if not enable:
            return {},

        params = {}
        if enable_temperature: params["temperature"] = temperature
        if enable_max_tokens: params["max_tokens"] = max_tokens
        if enable_top_p: params["top_p"] = top_p
        if enable_frequency_penalty: params["frequency_penalty"] = frequency_penalty
        if enable_presence_penalty: params["presence_penalty"] = presence_penalty
        return (params,)

