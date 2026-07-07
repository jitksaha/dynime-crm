"""
Serializers for Horilla Calendar models
"""

# Third-party imports (Django)
from rest_framework import serializers

# First party imports (Horilla)
from horilla.contrib.core.api.serializers import HorillaUserSerializer

# Local imports
from ..models import UserAvailability, UserCalendarPreference


class UserCalendarPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserCalendarPreference model"""

    user_details = HorillaUserSerializer(source="user", read_only=True)

    class Meta:
        """Meta class for UserCalendarPreferenceSerializer"""

        model = UserCalendarPreference
        fields = "__all__"


class UserAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for UserAvailability model"""

    user_details = HorillaUserSerializer(source="user", read_only=True)

    class Meta:
        """Meta class for UserAvailabilitySerializer"""

        model = UserAvailability
        fields = "__all__"
