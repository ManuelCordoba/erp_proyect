"""
URL routing for S3 Pre-signed URLs API and Document Management.
"""
from django.urls import path
from .views import (
    PresignedUploadURLView,
    PresignedDownloadURLView,
    DocumentCreateView,
    DocumentApproveView,
    DocumentRejectView,
)

app_name = 'documents'

urlpatterns = [
    # Generate pre-signed URL for upload
    path('presigned-upload-url/', PresignedUploadURLView.as_view(), name='presigned-upload-url'),
    
    # Generate pre-signed URL for download
    path('presigned-download-url/', PresignedDownloadURLView.as_view(), name='presigned-download-url'),
    
    # Create document record
    path('', DocumentCreateView.as_view(), name='document-create'),
    
    # Approve document
    path('<uuid:document_id>/approve/', DocumentApproveView.as_view(), name='document-approve'),
    
    # Reject document
    path('<uuid:document_id>/reject/', DocumentRejectView.as_view(), name='document-reject'),
]
