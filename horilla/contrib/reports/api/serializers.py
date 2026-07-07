"""
Serializers for horilla.contrib.reports models
"""

# Third-party imports (Django)
from rest_framework import serializers

# First party imports (Horilla)
from horilla.contrib.core.api.serializers import HorillaUserSerializer

# Local imports
from ..models import Report, ReportFolder


class ReportFolderSerializer(serializers.ModelSerializer):
    """Serializer for ReportFolder model"""

    report_folder_owner_details = HorillaUserSerializer(
        source="report_folder_owner", read_only=True
    )

    class Meta:
        """Meta options for ReportFolderSerializer."""

        model = ReportFolder
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model"""

    report_owner_details = HorillaUserSerializer(source="report_owner", read_only=True)
    folder_details = ReportFolderSerializer(source="folder", read_only=True)

    class Meta:
        """Meta options for ReportSerializer."""

        model = Report
        fields = "__all__"
