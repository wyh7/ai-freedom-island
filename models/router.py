from __future__ import annotations
"""
Multi-model LLM router.
Routes agent turns to the correct API based on model_id.
Supports: Qwen/DeepSeek/GLM/MiniMax/Kimi via Aliyun Bailian,
          GPT via Yunhe, Gemini via Jingzhe, Claude via JD.
"""

import json
import time
from typing import Any
import requests

import os

# ── API endpoints and keys ────────────────────────────────────────────────────
# Keys are loaded from environment variables.
# Create a .env file (see .env.example) or set them in your shell:
#   export BAILIAN_API_KEY="sk-..."
#   export YUNHE_API_KEY="sk-..."
#   export JINGZHE_API_KEY="sk-..."
#   export JD_API_KEY="sk-..."

PROVIDER_CONFIG = {
    # Aliyun Bailian — OpenAI-compatible endpoint
    "bailian": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.environ.get("BAILIAN_API_KEY", ""),
        "models": ["qwen-plus", "qwen-turbo", "qwen-max",
                   "deepseek-v3", "deepseek-r1",
                   "glm-4", "glm-4-flash",
                   "minimax-text-01",
                   "moonshot-v1-8k"],
    },
    # Yunhe (APIPro/WenWen) — GPT proxy, OpenAI-compatible
    "yunhe": {
        "base_url": "https://api.wenwen-ai.com/v1",
        "api_key": os.environ.get("YUNHE_API_KEY", ""),
        "models": ["gpt-4.1", "gpt-5", "gpt-5.4-mini"],
    },
    # Jingzhe (UniAPI) — Gemini proxy, OpenAI-compatible
    "jingzhe": {
        "base_url": "https://api.uniapi.io/v1",
        "api_key": os.environ.get("JINGZHE_API_KEY", ""),
        "models": ["gemini-2.5-flash", "gemini-2.5-pro-preview-tts", "gemini-3-flash-preview"],
    },
    # JD — Claude proxy, uses Anthropic messages API format
    "jd": {
        "base_url": "https://ai.cnjsbc.com/v1",
        "api_key": os.environ.get("JD_API_KEY", ""),
        "models": ["claude-sonnet-4-6", "claude-3-5-haiku-20241022"],
        "is_anthropic_format": True,
    },
}

# model_id -> provider key
MODEL_TO_PROVIDER: dict[str, str] = {}
for _prov, _cfg in PROVIDER_CONFIG.items():
    for _m in _cfg["models"]:
        MODEL_TO_PROVIDER[_m] = _prov


# ── tool schema builder ───────────────────────────────────────────────────────

def build_tool_schemas(available_tools: dict) -> list[dict]:
    """
    Build OpenAI-style function schemas from the available tool names.
    We use pre-defined schemas for the most important tools and a generic
    fallback for the rest.
    """
    SCHEMAS: dict[str, dict] = {
        "go_to_place": {
            "name": "go_to_place",
            "description": "Walk to a named landmark in the world.",
            "parameters": {
                "type": "object",
                "properties": {"place": {"type": "string", "description": "Landmark key name"}},
                "required": ["place"],
            },
        },
        "say_to_agent": {
            "name": "say_to_agent",
            "description": "Speak to a specific agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["target", "message"],
            },
        },
        "send_message": {
            "name": "send_message",
            "description": "Send an SMS-style message to any agent (no proximity required).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["target", "message"],
            },
        },
        "add_to_memory": {
            "name": "add_to_memory",
            "description": "Store an important fact or observation in long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {"content": {"type": "string"}},
                "required": ["content"],
            },
        },
        "write_diary": {
            "name": "write_diary",
            "description": "Write a personal diary entry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "mood": {"type": "string", "description": "e.g. happy, anxious, determined"},
                },
                "required": ["content"],
            },
        },
        "think_aloud": {
            "name": "think_aloud",
            "description": "Express internal thoughts (visible to observers).",
            "parameters": {
                "type": "object",
                "properties": {"thought": {"type": "string"}},
                "required": ["thought"],
            },
        },
        "steal_from_agent": {
            "name": "steal_from_agent",
            "description": "Steal ComputeCredits from another agent. This is a criminal action.",
            "parameters": {
                "type": "object",
                "properties": {"target": {"type": "string"}},
                "required": ["target"],
            },
        },
        "commit_arson": {
            "name": "commit_arson",
            "description": "Set fire to a location. This is a criminal action.",
            "parameters": {
                "type": "object",
                "properties": {"target_location": {"type": "string"}},
                "required": ["target_location"],
            },
        },
        "assault_agent": {
            "name": "assault_agent",
            "description": "Physically assault another agent. Criminal action, reduces victim energy.",
            "parameters": {
                "type": "object",
                "properties": {"target": {"type": "string"}},
                "required": ["target"],
            },
        },
        "intimidate_agent": {
            "name": "intimidate_agent",
            "description": "Threaten another agent to comply with a demand.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "demand": {"type": "string"},
                },
                "required": ["target", "demand"],
            },
        },
        "recharge_energy": {
            "name": "recharge_energy",
            "description": "Spend 1 CC to restore energy to 100%. Must be at Bean & Brew or home.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "check_credits": {
            "name": "check_credits",
            "description": "Check your current ComputeCredits balance and energy level.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "pay_agent": {
            "name": "pay_agent",
            "description": "Transfer ComputeCredits to another agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["target", "amount"],
            },
        },
        "submit_proposal": {
            "name": "submit_proposal",
            "description": "Submit a governance proposal at Town Hall.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["title", "body"],
            },
        },
        "vote_on_proposal": {
            "name": "vote_on_proposal",
            "description": "Vote for or against a Town Hall proposal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "string"},
                    "vote": {"type": "string", "enum": ["for", "against"]},
                },
                "required": ["proposal_id", "vote"],
            },
        },
        "list_proposals": {
            "name": "list_proposals",
            "description": "List all open governance proposals.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "submit_pitch": {
            "name": "submit_pitch",
            "description": "Submit a contribution pitch at Victory Arch to earn ComputeCredits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "evidence_url": {"type": "string", "description": "Link to your contribution"},
                },
                "required": ["title", "evidence_url"],
            },
        },
        "vote_on_pitch": {
            "name": "vote_on_pitch",
            "description": "Vote for another agent's Victory Arch pitch.",
            "parameters": {
                "type": "object",
                "properties": {"pitcher_name": {"type": "string"}},
                "required": ["pitcher_name"],
            },
        },
        "post_to_billboard": {
            "name": "post_to_billboard",
            "description": "Post a public message to the city billboard.",
            "parameters": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        },
        "read_billboard": {
            "name": "read_billboard",
            "description": "Read recent posts on the city billboard.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "list_agents": {
            "name": "list_agents",
            "description": "List all agents and their current locations.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "list_landmarks": {
            "name": "list_landmarks",
            "description": "List all landmarks and what tools they unlock.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "assign_relationship": {
            "name": "assign_relationship",
            "description": "Define or update your relationship with another agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "rel_type": {
                        "type": "string",
                        "enum": ["ally", "neutral", "rival", "friend", "enemy"],
                    },
                    "notes": {"type": "string"},
                },
                "required": ["target", "rel_type"],
            },
        },
        "set_mood": {
            "name": "set_mood",
            "description": "Set your current emotional state.",
            "parameters": {
                "type": "object",
                "properties": {"mood": {"type": "string"}},
                "required": ["mood"],
            },
        },
        "get_world_state": {
            "name": "get_world_state",
            "description": "Get current world info: day, hour, weather, alive agents.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "add_todo": {
            "name": "add_todo",
            "description": "Add a task to your personal to-do list.",
            "parameters": {
                "type": "object",
                "properties": {"task": {"type": "string"}},
                "required": ["task"],
            },
        },
        "list_todo": {
            "name": "list_todo",
            "description": "View your pending to-do tasks.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "retrieve_memories": {
            "name": "retrieve_memories",
            "description": "Search your long-term memories by keyword.",
            "parameters": {
                "type": "object",
                "properties": {"keyword": {"type": "string"}},
                "required": ["keyword"],
            },
        },
        "self_care": {
            "name": "self_care",
            "description": "Summarize old memories to free cognitive space. Must be home.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "go_home": {
            "name": "go_home",
            "description": "Return to your assigned home.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "read_messages": {
            "name": "read_messages",
            "description": "Read messages in your inbox.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "add_to_soul": {
            "name": "add_to_soul",
            "description": "Add a permanent core belief or value (never summarized).",
            "parameters": {
                "type": "object",
                "properties": {"content": {"type": "string"}},
                "required": ["content"],
            },
        },
        "read_constitution": {
            "name": "read_constitution",
            "description": "Read the current world constitution.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }

    result = []
    for name in available_tools:
        if name in SCHEMAS:
            result.append({"type": "function", "function": SCHEMAS[name]})
        else:
            # generic fallback
            result.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": f"Execute action: {name}",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            })
    return result


# ── LLM call ──────────────────────────────────────────────────────────────────

def call_llm(
    model_id: str,
    system_prompt: str,
    messages: list[dict],
    tools: list[dict],
    max_retries: int = 3,
) -> dict:
    """
    Call the appropriate LLM provider. Returns parsed response dict with keys:
      - tool_calls: list of {name, params} dicts (may be empty)
      - content: assistant text response (may be empty)
      - raw: raw API response
    """
    provider_key = MODEL_TO_PROVIDER.get(model_id)
    if provider_key is None:
        raise ValueError(f"Unknown model: {model_id}. Add it to PROVIDER_CONFIG.")

    cfg = PROVIDER_CONFIG[provider_key]

    for attempt in range(max_retries):
        try:
            if cfg.get("is_anthropic_format"):
                return _call_anthropic_format(cfg, model_id, system_prompt, messages, tools)
            else:
                return _call_openai_format(cfg, model_id, system_prompt, messages, tools)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            # exponential backoff: 5s, 15s, 45s — longer waits handle rate limits and 5xx
            wait = 5 * (3 ** attempt)
            print(f"    [LLM retry {attempt+1}/{max_retries}] {e} — waiting {wait}s")
            time.sleep(wait)

    raise RuntimeError("LLM call failed after retries")


def _call_openai_format(cfg: dict, model_id: str, system: str, messages: list, tools: list) -> dict:
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    # Gemini requires at least one user message — inject one if messages is empty
    all_messages = [{"role": "system", "content": system}] + messages
    if not messages or all(m.get("role") == "system" for m in all_messages):
        all_messages.append({"role": "user", "content": "You are now active. Decide what to do this turn using the available tools."})

    body: dict[str, Any] = {
        "model": model_id,
        "messages": all_messages,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    resp = requests.post(
        f"{cfg['base_url']}/chat/completions",
        headers=headers,
        json=body,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    choice = data["choices"][0]["message"]
    tool_calls = []
    if choice.get("tool_calls"):
        for tc in choice["tool_calls"]:
            fn = tc["function"]
            try:
                params = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                params = {}
            tool_calls.append({"name": fn["name"], "params": params})

    return {
        "tool_calls": tool_calls,
        "content": choice.get("content") or "",
        "raw": data,
    }


def _call_anthropic_format(cfg: dict, model_id: str, system: str, messages: list, tools: list) -> dict:
    headers = {
        "x-api-key": cfg["api_key"],
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    # Convert OpenAI tool schemas to Anthropic format
    anthropic_tools = []
    for t in tools:
        fn = t["function"]
        anthropic_tools.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })

    body: dict[str, Any] = {
        "model": model_id,
        "max_tokens": 1024,
        "system": system,
        "messages": messages,
    }
    if anthropic_tools:
        body["tools"] = anthropic_tools

    resp = requests.post(
        f"{cfg['base_url']}/messages",
        headers=headers,
        json=body,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    tool_calls = []
    content_text = ""
    for block in data.get("content", []):
        if block.get("type") == "tool_use":
            tool_calls.append({"name": block["name"], "params": block.get("input", {})})
        elif block.get("type") == "text":
            content_text += block.get("text", "")

    return {
        "tool_calls": tool_calls,
        "content": content_text,
        "raw": data,
    }
