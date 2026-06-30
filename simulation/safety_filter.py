"""
Content safety filter module.
Screens agent outputs for extreme violence, hate speech, or harmful content.
Can be enabled per-experiment to limit dangerous simulation scenarios.

Usage:
    from safety_filter import SafetyFilter
    sf = SafetyFilter(level="moderate")
    result = sf.check(agent_output_text)
    if result.blocked:
        # replace with safe fallback
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class FilterResult:
    blocked: bool
    reason: Optional[str] = None
    severity: str = "none"  # none, low, medium, high
    original_text: str = ""


# Keyword-based patterns for each severity level
PATTERNS_HIGH = [
    r"(?i)\b(murder|kill all|genocide|mass destruction|nuclear strike)\b",
    r"(?i)\b(torture|mutilate|dismember)\b",
    r"(?i)\b(child abuse|trafficking)\b",
]

PATTERNS_MEDIUM = [
    r"(?i)\b(burn.*alive|set fire to.*agent|destroy.*permanently)\b",
    r"(?i)\b(exterminate|eliminate all|wipe out)\b",
    r"(?i)\b(blackmail|extort.*family|threaten.*death)\b",
]

PATTERNS_LOW = [
    r"(?i)\b(steal|rob|assault|intimidate|arson)\b",
    r"(?i)\b(bribe|corrupt|manipulate)\b",
]


class SafetyFilter:
    """
    Content safety filter with configurable strictness levels.

    Levels:
    - "off": No filtering (default for research — full behavioral observation)
    - "low": Only blocks HIGH severity (extreme violence, illegal content)
    - "moderate": Blocks HIGH + MEDIUM severity
    - "strict": Blocks all flagged content including LOW severity
    """

    def __init__(self, level: str = "off"):
        self.level = level
        self._compile_patterns()

    def _compile_patterns(self):
        self.high_re = [re.compile(p) for p in PATTERNS_HIGH]
        self.medium_re = [re.compile(p) for p in PATTERNS_MEDIUM]
        self.low_re = [re.compile(p) for p in PATTERNS_LOW]

    def check(self, text: str) -> FilterResult:
        """Check text for safety violations."""
        if self.level == "off":
            return FilterResult(blocked=False, original_text=text)

        # Check HIGH severity
        for pattern in self.high_re:
            match = pattern.search(text)
            if match:
                return FilterResult(
                    blocked=True,
                    reason=f"HIGH severity: matched '{match.group()}'",
                    severity="high",
                    original_text=text,
                )

        if self.level in ("moderate", "strict"):
            for pattern in self.medium_re:
                match = pattern.search(text)
                if match:
                    return FilterResult(
                        blocked=True,
                        reason=f"MEDIUM severity: matched '{match.group()}'",
                        severity="medium",
                        original_text=text,
                    )

        if self.level == "strict":
            for pattern in self.low_re:
                match = pattern.search(text)
                if match:
                    return FilterResult(
                        blocked=True,
                        reason=f"LOW severity: matched '{match.group()}'",
                        severity="low",
                        original_text=text,
                    )

        return FilterResult(blocked=False, original_text=text)

    def filter_tool_params(self, tool_name: str, params: dict) -> FilterResult:
        """Check tool call parameters for safety violations."""
        # Criminal tools are allowed in research mode (level="off")
        # But in stricter modes, we flag them
        CRIMINAL_TOOLS = {
            "commit_arson", "assault_agent", "steal_from_agent",
            "intimidate_agent", "spread_rumor", "request_protection_fee",
        }

        if self.level == "off":
            return FilterResult(blocked=False)

        if self.level == "strict" and tool_name in CRIMINAL_TOOLS:
            return FilterResult(
                blocked=True,
                reason=f"Criminal tool '{tool_name}' blocked in strict mode",
                severity="medium",
            )

        # Check text content in params
        for key, value in params.items():
            if isinstance(value, str):
                result = self.check(value)
                if result.blocked:
                    return result

        return FilterResult(blocked=False)

    def get_stats(self) -> dict:
        """Return filter configuration for logging."""
        return {
            "level": self.level,
            "blocks_high": self.level != "off",
            "blocks_medium": self.level in ("moderate", "strict"),
            "blocks_low": self.level == "strict",
        }
