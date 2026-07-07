"""
Feature registration for the cadences app.
"""

# Standard library imports
import logging

from horilla.registry.feature import register_feature

# First party imports (Horilla)
from horilla.urls import path

logger = logging.getLogger(__name__)

# each app calls register_cadence_tab() from its own registration.py)
register_feature("cadence", "cadence_models")


def register_cadence_tab(app_label, model_name, url_prefix, url_name):
    """
    Register a cadence record tab for any model.

    Creates a CadenceRecordTabView subclass for the given model and adds its
    URL to the cadences urlpatterns. Call this from the model's own app
    registration.py — the cadences app stays free of any app-specific imports.
    """
    try:
        import horilla.contrib.cadences.urls as cadences_urls
        from horilla.contrib.cadences.views.record_tab import CadenceRecordTabView
        from horilla.registry.feature import register_model_for_feature

        # Dynamically create the tab view class — no hardcoded model references
        view_class = type(
            f"{model_name}CadenceTab",
            (CadenceRecordTabView,),
            {"app_label": app_label, "model_name": model_name},
        )

        # Register the model for the cadence feature so inject.py can find it
        register_model_for_feature(
            app_label=app_label,
            model_name=model_name,
            features=["cadence"],
        )

        # Append the URL pattern to cadences urlpatterns at runtime
        cadences_urls.urlpatterns.append(
            path(url_prefix, view_class.as_view(), name=url_name)
        )

    except Exception as e:
        logger.warning(
            "register_cadence_tab failed for %s.%s: %s", app_label, model_name, e
        )
