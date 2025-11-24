"""
Serializers for S3 Pre-signed URLs API endpoints and Document Management.
"""
from rest_framework import serializers
from .models import Company, DomainEntity, Document, DocumentValidation, Approver


class PresignedUploadSerializer(serializers.Serializer):
    """Serializer for generating presigned upload URL."""
    file_name = serializers.CharField(required=True, help_text="Name of the file to upload")
    content_type = serializers.CharField(required=True, help_text="MIME type of the file (e.g., 'image/jpeg', 'application/pdf')")
    bucket_key = serializers.CharField(required=False, allow_blank=True, help_text="Optional S3 bucket key/path. If not provided, will be auto-generated")


class PresignedDownloadSerializer(serializers.Serializer):
    """Serializer for generating presigned download URL."""
    bucket_key = serializers.CharField(required=True, help_text="S3 bucket key/path of the file to download")


class PresignedUploadResponseSerializer(serializers.Serializer):
    """Serializer for presigned upload URL response."""
    upload_url = serializers.URLField(help_text="Pre-signed URL for uploading the file (use POST method)")
    fields = serializers.DictField(help_text="Form fields required for the upload POST request")
    bucket_key = serializers.CharField(help_text="S3 bucket key/path where the file will be stored")


class PresignedDownloadResponseSerializer(serializers.Serializer):
    """Serializer for presigned download URL response."""
    download_url = serializers.URLField(help_text="Pre-signed URL for downloading the file")
    bucket_key = serializers.CharField(help_text="S3 bucket key/path of the file")


# Document Creation Serializers
class ApproverUUIDField(serializers.UUIDField):
    """
    Custom UUID field that validates that the Approver exists.
    """
    def to_internal_value(self, data):
        """Validate and return the approver UUID."""
        value = super().to_internal_value(data)
        try:
            Approver.objects.get(id=value)
        except Approver.DoesNotExist:
            raise serializers.ValidationError(f"Approver with ID {value} does not exist.")
        return value


class ValidationStepSerializer(serializers.Serializer):
    """Serializer for validation flow steps."""
    order = serializers.IntegerField(min_value=1, help_text="Step order number")
    approver_user_id = ApproverUUIDField(help_text="UUID of the approver who must approve this step")


class ValidationFlowSerializer(serializers.Serializer):
    """Serializer for validation flow configuration."""
    enabled = serializers.BooleanField(help_text="Whether validation flow is enabled")
    steps = ValidationStepSerializer(many=True, help_text="List of validation steps")

    def validate_steps(self, value):
        """Validate that step orders are unique and sequential."""
        if not value:
            return value
        
        orders = [step['order'] for step in value]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError("Step orders must be unique.")
        if sorted(orders) != list(range(1, len(orders) + 1)):
            raise serializers.ValidationError("Step orders must be sequential starting from 1.")
        return value


class EntitySerializer(serializers.Serializer):
    """Serializer for entity information."""
    entity_type = serializers.CharField(help_text="Type of entity (e.g., 'vehicle', 'employee')")
    entity_id = serializers.UUIDField(help_text="UUID of the entity")
    
    def validate_entity_type(self, value):
        """Convert entity_type to uppercase to match model choices."""
        value_upper = value.upper()
        valid_types = ['VEHICLE', 'EMPLOYEE', 'OTHER']
        if value_upper not in valid_types:
            raise serializers.ValidationError(
                f"Entity type must be one of: {', '.join(valid_types).lower()}"
            )
        return value_upper


class DocumentDataSerializer(serializers.Serializer):
    """Serializer for document data."""
    name = serializers.CharField(help_text="Name of the document")
    mime_type = serializers.CharField(help_text="MIME type of the document")
    size_bytes = serializers.IntegerField(min_value=0, help_text="Size of the document in bytes")
    bucket_key = serializers.CharField(help_text="S3 bucket key/path or UUID of the document")


class DocumentCreateSerializer(serializers.Serializer):
    """Serializer for creating a document."""
    company_id = serializers.UUIDField(help_text="UUID of the company")
    entity = EntitySerializer(help_text="Entity information")
    document = DocumentDataSerializer(help_text="Document information")
    validation_flow = ValidationFlowSerializer(required=False, allow_null=True, help_text="Validation flow configuration")

    def validate_company_id(self, value):
        """Validate that company exists."""
        try:
            Company.objects.get(id=value)
        except Company.DoesNotExist:
            raise serializers.ValidationError("Company does not exist.")
        return value

    def validate(self, data):
        """Validate validation flow steps."""
        # Validation of approvers is now handled by ApproverUUIDField
        # This method can be used for additional cross-field validation if needed
        return data


class DocumentResponseSerializer(serializers.ModelSerializer):
    """Serializer for document response."""
    class Meta:
        model = Document
        fields = [
            'id', 'name', 'size', 'mime_type',
            'bucket_key', 'validation_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApproveRejectSerializer(serializers.Serializer):
    """Serializer for approving or rejecting a document."""
    approver_user_id = ApproverUUIDField(help_text="UUID of the approver (Approver UUID)")
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Reason for approval or rejection")
