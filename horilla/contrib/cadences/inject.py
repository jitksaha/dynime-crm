"""Runtime injection for cadence tab visibility in Horilla generic detail views."""

# Standard library imports
import logging
from functools import wraps

# First-party (Horilla)
from horilla.contrib.generics.views import HorillaDetailTabView

logger = logging.getLogger(__name__)


def _get_cadence_tab_model(self):
    """
    Resolve the model class for the cadence tab by reading app_label/model_name
    from the CadenceRecordTabView subclass registered at the cadence URL.
    This mirrors how ContactCadenceTab/AccountCadenceTab declare their model.
    """
    try:
        from horilla.apps import apps
        from horilla.urls import resolve

        cadence_url_name = self.urls.get("cadences", "")
        if not cadence_url_name:
            return None

        # Build a dummy URL path to resolve the view class from the URL name
        from horilla.urls import reverse_lazy

        dummy_url = str(reverse_lazy(cadence_url_name, kwargs={"pk": 0}))
        match = resolve(dummy_url)
        view_class = getattr(match.func, "view_class", None)
        if view_class is None:
            return None

        app_label = getattr(view_class, "app_label", None)
        model_name = getattr(view_class, "model_name", None)
        if not app_label or not model_name:
            return None

        return apps.get_model(app_label, model_name)
    except Exception:
        return None


def _has_active_cadences_for_model(model):
    """Return True if any active cadences exist for the given model class."""
    try:
        from horilla.contrib.cadences.models import Cadence
        from horilla.contrib.core.models import HorillaContentType

        content_type = HorillaContentType.objects.get_for_model(model)
        return Cadence.objects.filter(module=content_type, is_active=True).exists()
    except Exception:
        return True


def _create_prepare_tabs_with_cadence_check(original_prepare_tabs):
    @wraps(original_prepare_tabs)
    def _prepare_detail_tabs_with_cadence_check(self):
        original_prepare_tabs(self)

        cadence_tab_index = next(
            (i for i, t in enumerate(self.tabs) if t.get("id") == "cadence"), None
        )
        if cadence_tab_index is None:
            return

        try:
            model = _get_cadence_tab_model(self)
            if model is None:
                return

            if not _has_active_cadences_for_model(model):
                self.tabs.pop(cadence_tab_index)
        except Exception as e:
            logger.debug("Could not evaluate cadence tab visibility: %s", e)

    return _prepare_detail_tabs_with_cadence_check


def inject_cadence_tab():
    """Wrap HorillaDetailTabView._prepare_detail_tabs to hide the cadence tab
    when no active cadences exist for the model."""
    try:
        if not hasattr(HorillaDetailTabView, "_original_prepare_detail_tabs_cadence"):
            HorillaDetailTabView._original_prepare_detail_tabs_cadence = (
                HorillaDetailTabView._prepare_detail_tabs
            )
            HorillaDetailTabView._prepare_detail_tabs = (
                _create_prepare_tabs_with_cadence_check(
                    HorillaDetailTabView._original_prepare_detail_tabs_cadence
                )
            )
    except Exception as e:
        logger.warning("Failed to inject cadence tab visibility check: %s", e)


inject_cadence_tab()
