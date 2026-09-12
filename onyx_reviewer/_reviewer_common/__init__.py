"""Shared, product-specific review contracts used by Reviewer editions."""

from .catalog import BASE_RULES, RULE_BY_ID, RuleDefinition
from .palettes import (
    BASE_STYLE_IDS,
    DEFAULT_PALETTE,
    FindingStyle,
    PALETTE_ENUM_ITEMS,
    base_finding_style,
    base_palette_styles,
    fallback_style,
    normalize_palette_id,
    palette_ids,
)
from .results import Finding, ObjectResult, ReviewReport, REPORT_SCHEMA

__all__ = (
    "BASE_RULES",
    "RULE_BY_ID",
    "RuleDefinition",
    "BASE_STYLE_IDS",
    "DEFAULT_PALETTE",
    "FindingStyle",
    "PALETTE_ENUM_ITEMS",
    "base_finding_style",
    "base_palette_styles",
    "fallback_style",
    "normalize_palette_id",
    "palette_ids",
    "Finding",
    "ObjectResult",
    "ReviewReport",
    "REPORT_SCHEMA",
)
