"""Queryset utilities shared across Horilla contrib apps."""

# Standard library imports
import logging

# Third-party imports (Django)
from horilla.db.models import Q

logger = logging.getLogger(__name__)

__all__ = ["apply_conditions", "get_queryset_for_module"]


def get_queryset_for_module(user, model):
    """
    Returns queryset for a given model based on user permissions.
    Uses model.OWNER_FIELDS if available.
    """
    app_label = model._meta.app_label
    model_name = model._meta.model_name

    if user.has_perm(f"{app_label}.view_{model_name}"):
        return model.objects.all()

    if user.has_perm(f"{app_label}.view_own_{model_name}"):
        owner_fields = getattr(model, "OWNER_FIELDS", [])
        if not owner_fields:
            return model.objects.none()

        q_filter = Q()
        for field in owner_fields:
            q_filter |= Q(**{field: user})
        return model.objects.filter(q_filter)

    return model.objects.none()


def apply_conditions(queryset, conditions):
    """Apply filter conditions to a queryset with proper type handling."""

    for condition in conditions:
        field = condition.field
        operator = condition.operator
        value = condition.value

        if not value and operator not in [
            "is_null",
            "is_not_null",
            "isnull",
            "isnotnull",
        ]:
            continue

        try:
            model = queryset.model
            field_obj = model._meta.get_field(field)

            converted_value = value
            if hasattr(field_obj, "get_internal_type"):
                field_type = field_obj.get_internal_type()

                if field_type in [
                    "IntegerField",
                    "BigIntegerField",
                    "SmallIntegerField",
                    "PositiveIntegerField",
                    "PositiveSmallIntegerField",
                    "DecimalField",
                    "FloatField",
                ]:
                    try:
                        if field_type in ["DecimalField", "FloatField"]:
                            converted_value = float(value)
                        else:
                            converted_value = int(value)
                    except (ValueError, TypeError):
                        logger.warning(
                            "Could not convert value '%s' to numeric for field '%s'",
                            value,
                            field,
                        )
                        continue

                elif field_type == "BooleanField":
                    if str(value).lower() in ["true", "1", "yes"]:
                        converted_value = True
                    elif str(value).lower() in ["false", "0", "no"]:
                        converted_value = False
                    else:
                        logger.warning(
                            "Invalid boolean value '%s' for field '%s'",
                            value,
                            field,
                        )
                        continue

                elif field_type == "ForeignKey":
                    try:
                        converted_value = int(value)
                    except (ValueError, TypeError):
                        logger.warning(
                            "Could not convert FK value '%s' to int for field '%s'",
                            value,
                            field,
                        )
                        continue

            if operator in ["equals", "exact"]:
                queryset = queryset.filter(**{field: converted_value})

            elif operator in ["not_equals", "ne"]:
                queryset = queryset.exclude(**{field: converted_value})

            elif operator == "greater_than":
                queryset = queryset.filter(**{f"{field}__gt": converted_value})

            elif operator == "less_than":
                queryset = queryset.filter(**{f"{field}__lt": converted_value})

            elif operator in ["greater_equal", "gte"]:
                queryset = queryset.filter(**{f"{field}__gte": converted_value})

            elif operator in ["less_equal", "lte"]:
                queryset = queryset.filter(**{f"{field}__lte": converted_value})

            elif operator == "gt":
                queryset = queryset.filter(**{f"{field}__gt": converted_value})

            elif operator == "lt":
                queryset = queryset.filter(**{f"{field}__lt": converted_value})

            elif operator in ["contains", "icontains"]:
                queryset = queryset.filter(**{f"{field}__icontains": value})

            elif operator == "not_contains":
                queryset = queryset.exclude(**{f"{field}__icontains": value})

            elif operator in ["starts_with", "istartswith"]:
                queryset = queryset.filter(**{f"{field}__istartswith": value})

            elif operator in ["ends_with", "iendswith"]:
                queryset = queryset.filter(**{f"{field}__iendswith": value})

            elif operator in ["is_null", "isnull"]:
                queryset = queryset.filter(**{f"{field}__isnull": True})

            elif operator in ["is_not_null", "isnotnull"]:
                queryset = queryset.filter(**{f"{field}__isnull": False})

            elif operator == "in":
                values = [v.strip() for v in str(value).split(",")]
                queryset = queryset.filter(**{f"{field}__in": values})

            elif operator == "not_in":
                values = [v.strip() for v in str(value).split(",")]
                queryset = queryset.exclude(**{f"{field}__in": values})

        except Exception as e:
            logger.error(
                "Error applying condition %s %s %s: %s", field, operator, value, e
            )
            continue

    return queryset
