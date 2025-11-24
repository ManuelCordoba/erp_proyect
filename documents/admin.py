from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Company,
    DomainEntity,
    Document,
    DocumentValidation,
    Approver
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'nit', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'nit']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(DomainEntity)
class DomainEntityAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_type', 'object_id', 'created_at']
    list_filter = ['entity_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


class DocumentValidationInline(admin.TabularInline):
    """Inline to display validations within the Document admin."""
    model = DocumentValidation
    extra = 0
    fields = ['step_order', 'step_name', 'status', 'assigned_approver', 'actor_approver', 'action_date']
    readonly_fields = ['created_at', 'action_date', 'updated_at']
    ordering = ['step_order']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'company',
        'document_type',
        'validation_status',
        'size_mb_display',
        'creator',
        'created_at'
    ]
    list_filter = [
        'company',
        'document_type',
        'validation_status',
        'created_at'
    ]
    search_fields = ['name', 'file_hash', 'bucket_key']
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_download_date',
        'size_mb_display'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'document_type', 'company', 'domain_entity', 'creator')
        }),
        ('File Metadata', {
            'fields': ('size', 'size_mb_display', 'mime_type', 'file_hash', 'bucket_key')
        }),
        ('Validation', {
            'fields': ('validation_status',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'last_download_date')
        }),
    )
    inlines = [DocumentValidationInline]

    def size_mb_display(self, obj):
        """Displays the size in MB."""
        return f"{obj.size_mb} MB"
    size_mb_display.short_description = 'Size (MB)'


@admin.register(DocumentValidation)
class DocumentValidationAdmin(admin.ModelAdmin):
    list_display = [
        'document',
        'step_order',
        'step_name',
        'status_display',
        'assigned_approver',
        'actor_approver',
        'action_date',
        'created_at'
    ]
    list_filter = [
        'status',
        'assigned_approver',
        'actor_approver',
        'created_at',
        'action_date'
    ]
    search_fields = [
        'document__name',
        'step_name',
        'reason',
        'assigned_approver__user__username',
        'actor_approver__user__username'
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'document', 'step_order', 'step_name')
        }),
        ('Status and Assignment', {
            'fields': ('status', 'assigned_approver')
        }),
        ('Action Performed', {
            'fields': ('actor_approver', 'reason', 'action_date')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    ordering = ['document', 'step_order']
    date_hierarchy = 'created_at'

    def status_display(self, obj):
        """Displays the status with color."""
        colors = {
            'P': 'orange',
            'A': 'green',
            'R': 'red'
        }
        texts = {
            'P': '⏳ Pending',
            'A': '✓ Approved',
            'R': '✗ Rejected'
        }
        color = colors.get(obj.status, 'black')
        text = texts.get(obj.status, obj.get_status_display())
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            text
        )
    status_display.short_description = 'Status'


@admin.register(Approver)
class ApproverAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
