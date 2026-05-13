"""Reference-led reproduction workflow.

This skill turns a vague build request into a disciplined operator loop:
reference open, editor open, global surfaces first, then section-by-section
reproduction using the closest existing primitive.
"""
from __future__ import annotations

from typing import Any


def reference_led_reproduction_workflow(
    target: str,
    references: list[str] | None = None,
    scope: str = "full_surface",
    copy_mode: str = "faithful",
    constraints: list[str] | None = None,
) -> dict[str, Any]:
    """Return an execution plan for faithful UI/system reproduction work."""
    references = references or []
    constraints = constraints or []
    return {
        "target": target,
        "scope": scope,
        "copy_mode": copy_mode,
        "references": references,
        "constraints": constraints,
        "principles": [
            "truth_over_comfort: verify rendered output instead of trusting file edits",
            "two_surfaces_open: keep target reference and live editor/preview visible",
            "global_before_local: header, footer, navigation, tokens, fonts, color systems first",
            "reuse_before_create: find the closest existing primitive, duplicate it, then adapt",
            "merchant_or_operator_control: expose text, media, links, spacing, colors and states in schema/settings",
            "tokens_not_literals: use theme/system tokens for colors and fonts; hardcoded values require a reason",
            "section_loop: build one section, push, preview, compare, fix, then move to the next",
            "polish_after_fidelity: hover, glow, animation and micro-interactions come after structure matches",
            "copy_means_copy: if the order is faithful reproduction, deviations are defects unless explicitly chosen",
        ],
        "phases": [
            "inventory_target_and_references",
            "map_global_surfaces",
            "build_header_footer_navigation",
            "for_each_page_top_to_bottom",
            "for_each_section_choose_duplicate_adapt_test",
            "schema_and_editor_usability_pass",
            "visual_fidelity_pass_desktop_mobile",
            "links_routes_forms_empty_states_pass",
            "polish_effects_motion_accessibility_pass",
            "final_crawl_checkpoint_report",
        ],
        "section_loop": [
            "capture_reference_section_goal",
            "search_existing_sections_or_components_for_nearest_shape",
            "duplicate_or_create_from_nearest_primitive",
            "adapt_markup_styles_assets_and_schema",
            "bind_editable_settings_for_every_merchant_or_operator_facing_part",
            "push_or_build_small_delta",
            "preview_actual_render",
            "compare_against_reference",
            "fix_until_delta_is_intentional",
            "record_decision_and_next_section",
        ],
        "quality_gates": [
            "route_returns_200",
            "expected_content_markers_present",
            "editor_fields_cover_text_images_links_colors_spacing",
            "no_unintended_global_wipe",
            "no_hidden_long_running_process",
            "mobile_no_overlap",
            "interactive_states_visible",
            "checkpoint_written",
        ],
        "transfer_domains": [
            "shopify_theme_work",
            "frontend_rebuilds",
            "design_system_migration",
            "automation_workflows",
            "athos_self_improvement",
            "hardware_or_device_onboarding",
            "operations_playbooks",
        ],
    }
