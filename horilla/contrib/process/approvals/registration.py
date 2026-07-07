"""
Feature registration for Approvals app.

This declares the "approvals" feature and its registry key ("approval_models"),
so other apps can opt-in their models without modifying their model code.
"""

# First party imports (Horilla)
from horilla.registry.feature import register_feature

register_feature(
    "approvals",
    "approval_models",
    auto_register_all=False,
)
