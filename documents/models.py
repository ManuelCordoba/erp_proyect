from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import uuid


class Approver(models.Model):
    """
    Model to represent approvers with UUID primary key.
    This allows using UUID for approvers while keeping Django's User model unchanged.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='approver_profile',
        verbose_name="User",
        help_text="Django User associated with this approver"
    )
    active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Update Date")

    class Meta:
        verbose_name = "Approver"
        verbose_name_plural = "Approvers"
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"


class Company(models.Model):
    """
    Model to store companies in the ERP system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Company Name")
    nit = models.CharField(max_length=50, unique=True, verbose_name="NIT")
    active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Update Date")

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ['name']

    def __str__(self):
        return self.name


class DomainEntity(models.Model):
    """
    Domain entity to which documents are associated.
    """
    ENTITY_TYPE = [
            ('VEHICLE', 'vehicle'),
            ('EMPLOYEE', 'employee'),
            ('OTHER', 'other'),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Generic Foreign Key to relate to any model
    entity_type = models.CharField(
        max_length=10,
        choices=ENTITY_TYPE,
        verbose_name="Entity type",
        help_text="Entity type"
    )
    object_id = models.UUIDField()
    
    # Additional metadata
    name = models.CharField(max_length=255, verbose_name="Entity Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Update Date")

    class Meta:
        verbose_name = "Domain Entity"
        verbose_name_plural = "Domain Entities"
        indexes = [
            models.Index(fields=['entity_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.name} ({self.entity_type})"


class Document(models.Model):
    """
    Main model to store documents and their metadata.
    """
    VALIDATION_STATUS_CHOICES = [
        (None, 'No Validation'),
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('R', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Main relationships
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Company"
    )
    domain_entity = models.ForeignKey(
        DomainEntity,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Domain Entity"
    )
    
    # File metadata
    name = models.CharField(max_length=255, verbose_name="Document Name")
    size = models.BigIntegerField(verbose_name="Size (bytes)", validators=[MinValueValidator(0)])
    mime_type = models.CharField(max_length=100, verbose_name="MIME Type")
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="File Hash (SHA-256)"
    )
    
    # Bucket location
    bucket_key = models.CharField(
        max_length=500,
        unique=True,
        verbose_name="Bucket Path",
        help_text="Full path or file ID in the storage bucket (must be unique)"
    )
    
    # Validation status (calculated from DocumentValidation)
    validation_status = models.CharField(
        max_length=1,
        choices=VALIDATION_STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name="Validation Status",
        help_text="Overall status calculated from validations"
    )
    
    # User who created the document
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_created',
        verbose_name="Creator User"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Update Date")
    last_download_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Download Date"
    )

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'validation_status']),
            models.Index(fields=['domain_entity']),
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    @property
    def size_mb(self):
        """Returns the size in megabytes."""
        return round(self.size / (1024 * 1024), 2)

    def get_pending_validation_for_approver(self, approver):
        """
        Get the pending validation assigned to a specific approver.
        
        Args:
            approver: Approver instance
            
        Returns:
            DocumentValidation instance or None
        """
        return self.validations.filter(
            assigned_approver=approver,
            status='P'
        ).order_by('step_order').first()

    def update_validation_status(self):
        """
        Update validation_status based on the current state of all validations.
        This method calculates the overall status:
        - 'R' (Rejected) if any validation is rejected
        - 'A' (Approved) if all validations are approved
        - 'P' (Pending) if there are pending validations and none are rejected
        - None if there are no validations
        """
        if not self.validations.exists():
            self.validation_status = None
            self.save(update_fields=['validation_status'])
            return
        
        all_validations = self.validations.all()
        pending_count = all_validations.filter(status='P').count()
        rejected_count = all_validations.filter(status='R').count()
        
        if rejected_count > 0:
            self.validation_status = 'R'
        elif pending_count == 0:
            # All validations approved
            self.validation_status = 'A'
        else:
            self.validation_status = 'P'
        
        self.save(update_fields=['validation_status'])


class DocumentValidation(models.Model):
    """
    Single table to manage all document validations.
    Each record represents a validation step for a specific document.
    Includes all necessary information for complete traceability.
    """
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('R', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='validations',
        verbose_name="Document"
    )
    
    # Validation step information
    step_order = models.PositiveIntegerField(
        verbose_name="Step Order",
        validators=[MinValueValidator(1)],
        help_text="Order number of the step in the validation flow"
    )
    step_name = models.CharField(
        max_length=255,
        verbose_name="Step Name",
        help_text="Descriptive name of the validation step"
    )
    
    # Approver assigned to approve (using UUID)
    assigned_approver = models.ForeignKey(
        'Approver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_assigned',
        verbose_name="Assigned Approver",
        help_text="Approver who must approve or reject this validation"
    )
    
    # Actor approver (using UUID)
    actor_approver = models.ForeignKey(
        'Approver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_performed',
        verbose_name="Actor Approver",
        help_text="Approver who approved or rejected the validation"
    )
    # Validation status
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='P',
        verbose_name="Status"
    )
    reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Reason/Comment",
        help_text="Reason or comment about the approval or rejection"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creation Date",
        help_text="Date when the validation record was created"
    )
    action_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Action Date",
        help_text="Date when the validation was approved or rejected"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Update Date"
    )

    class Meta:
        verbose_name = "Document Validation"
        verbose_name_plural = "Document Validations"
        ordering = ['document', 'step_order']
        unique_together = [['document', 'step_order']]
        indexes = [
            models.Index(fields=['document', 'status']),
            models.Index(fields=['document', 'step_order']),
            models.Index(fields=['actor_approver', 'action_date']),
            models.Index(fields=['assigned_approver', 'status']),
        ]

    def __str__(self):
        status_display = self.get_status_display()
        return f"{self.document.name} - Step {self.step_order}: {self.step_name} ({status_display})"

    def save(self, *args, **kwargs):
        """Updates action_date when status changes to Approved or Rejected."""
        if self.status in ['A', 'R'] and not self.action_date:
            from django.utils import timezone
            self.action_date = timezone.now()
        super().save(*args, **kwargs)
