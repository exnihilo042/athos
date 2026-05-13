# ATHOS Reference-Led Reproduction

This is the operator pattern learned from the Shopify theme workstream. It is not Shopify-specific. It is a general method for turning a powerful but abstract engine into a situated builder.

## Core Idea

When the goal is faithful construction, Athos must not behave like a text-only LLM guessing from memory. Athos must behave like an experienced operator with the target reference and the execution surface open at the same time.

The model is:

1. Keep the target/reference visible.
2. Keep the editor/live execution surface visible.
3. Build global surfaces first.
4. Work section by section.
5. Reuse the closest existing primitive before creating a new one.
6. Expose every future operator-facing control.
7. Verify rendered output, not just code.
8. Polish only after structural fidelity exists.

## Why It Matters

A generic LLM tends to jump straight to generation. That creates a plausible output, not a faithful one.

Athos must add the missing layer:

- situational discipline;
- visual/reference anchoring;
- reuse of existing components;
- schema/settings completeness;
- live verification;
- operational memory;
- explicit quality gates.

## Generalized Loop

For any complex surface:

1. Inventory references, constraints, existing primitives and target outcome.
2. Identify shared/global surfaces first: navigation, shell, tokens, safety policy, permissions, routing.
3. For each page or module, move top to bottom.
4. For each section or capability, find the nearest existing primitive.
5. Duplicate/adapt the primitive instead of wiping the system.
6. Make every external-facing part configurable.
7. Render/test the actual result.
8. Compare against the reference.
9. Fix the delta.
10. Record the decision and continue.

## Transfer

This pattern applies to:

- Shopify/Liquid theme work;
- frontend rebuilds;
- design system migrations;
- Athos self-improvement;
- workflow automation;
- device onboarding;
- hardware/capability integration.

In every domain, "copy" means copy. "Inspired by" means adapt. Athos must not silently confuse the two.
