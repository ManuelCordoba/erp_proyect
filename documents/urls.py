"""
URL routing for S3 Pre-signed URLs API and Document Management.
"""
from django.urls import path
from .views import (
    PresignedUploadURLView,
    DocumentCreateView,
    DocumentApproveView,
    DocumentRejectView,
    DocumentDownloadView,
)

app_name = 'documents'

urlpatterns = [
    # Generate pre-signed URL for upload
    path('presigned-upload-url/', PresignedUploadURLView.as_view(), name='presigned-upload-url'),
    
    # Create document record
    path('', DocumentCreateView.as_view(), name='document-create'),
    
    # Download document by ID
    path('<uuid:document_id>/download/', DocumentDownloadView.as_view(), name='document-download'),
    
    # Approve document
    path('<uuid:document_id>/approve/', DocumentApproveView.as_view(), name='document-approve'),
    
    # Reject document
    path('<uuid:document_id>/reject/', DocumentRejectView.as_view(), name='document-reject'),
]
