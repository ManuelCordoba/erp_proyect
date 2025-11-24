"""
API Views for S3 Pre-signed URLs and Document Management.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
import logging

from .aws_services import generate_presigned_upload_url, generate_presigned_download_url, check_object_exists
from .serializers import (
    PresignedUploadSerializer,
    PresignedUploadResponseSerializer,
    PresignedDownloadSerializer,
    PresignedDownloadResponseSerializer,
    DocumentCreateSerializer,
    DocumentResponseSerializer,
    ApproveRejectSerializer,
)
from .models import Company, DomainEntity, Document, DocumentValidation, Approver
import uuid

logger = logging.getLogger(__name__)


class ErrorHandlerMixin:
    """
    Mixin to provide centralized error handling for API views.
    Provides consistent error responses across all views.
    """
    
    def handle_exception(self, exc):
        """
        Handle exceptions in a consistent way across all views.
        This method can be called manually from try/except blocks.
        
        Args:
            exc: Exception instance
            
        Returns:
            Response with error details
        """
        # Log the exception
        logger.error(f"Error in {self.__class__.__name__}: {str(exc)}", exc_info=True)
        
        # Handle specific exceptions with appropriate messages
        if isinstance(exc, Document.DoesNotExist):
            return Response(
                {'error': 'Document does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, Company.DoesNotExist):
            return Response(
                {'error': 'Company does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, Approver.DoesNotExist):
            return Response(
                {'error': 'Approver does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Handle generic exceptions
        error_message = f'Error processing request: {str(exc)}'
        return Response(
            {'error': error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



class PresignedUploadURLView(ErrorHandlerMixin, APIView):
    """
    API endpoint to generate pre-signed URL for uploading files to S3.
    POST /api/documents/presigned-upload-url/
    """
    
    def post(self, request):
        serializer = PresignedUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        file_name = serializer.validated_data['file_name']
        content_type = serializer.validated_data['content_type']
        bucket_key = serializer.validated_data.get('bucket_key')
        
        # Generate bucket key if not provided
        if not bucket_key:
            bucket_key = f"uploads/{uuid.uuid4()}/{file_name}"
        
        try:
            presigned_data = generate_presigned_upload_url(
                bucket_key=bucket_key,
                content_type=content_type
            )
            
            response_serializer = PresignedUploadResponseSerializer(presigned_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)

class DocumentDownloadView(ErrorHandlerMixin, APIView):
    """
    API endpoint to generate pre-signed URL for downloading a document by its ID.
    GET /api/documents/{document_id}/download/
    """
    
    def get(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id)
            
            download_url = generate_presigned_download_url(document.bucket_key)
            
            return Response({
                'download_url': download_url
            }, status=status.HTTP_200_OK)
        except Document.DoesNotExist:
            return Response(
                {'error': 'Document does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return self.handle_exception(e)



class DocumentCreateView(ErrorHandlerMixin, APIView):
    """
    API endpoint to create a document record in the database.
    POST /api/documents/
    """
    
    @transaction.atomic
    def post(self, request):
        serializer = DocumentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        company_id = data['company_id']
        entity_data = data['entity']
        document_data = data['document']
        validation_flow = data.get('validation_flow')
        
        try:
            # Get company
            company = Company.objects.get(id=company_id)
            
            # Get or create DomainEntity
            entity_type = entity_data['entity_type']  # Already uppercase from serializer
            entity_id = entity_data['entity_id']
            
            # Try to get existing domain entity
            domain_entity = DomainEntity.objects.filter(
                entity_type=entity_type,
                object_id=entity_id
            ).first()
            
            if not domain_entity:
                # Create new domain entity
                # Generate name from entity type and ID
                entity_name = f"{entity_type} {entity_id}"
                
                domain_entity = DomainEntity.objects.create(
                    entity_type=entity_type,
                    object_id=entity_id,
                    name=entity_name
                )
            
            # Validate that the file exists in S3
            bucket_key = document_data['bucket_key']
            try:
                if not check_object_exists(bucket_key):
                    return Response(
                        {'error': f'File with bucket_key "{bucket_key}" does not exist in S3.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                return Response(
                    {'error': f'Error validating file in S3: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Check if document with this bucket_key already exists
            if Document.objects.filter(bucket_key=bucket_key).exists():
                return Response(
                    {'error': f'A document with bucket_key "{bucket_key}" already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create document
            document = Document.objects.create(
                company=company,
                domain_entity=domain_entity,
                name=document_data['name'],
                mime_type=document_data['mime_type'],
                size=document_data['size_bytes'],
                bucket_key=document_data['bucket_key'],
                validation_status='P' if validation_flow and validation_flow.get('enabled') else None,
                creator=request.user if request.user.is_authenticated else None
            )
            
            # Create validation steps if validation flow is enabled
            if validation_flow and validation_flow.get('enabled'):
                steps = validation_flow.get('steps', [])
                
                for step_data in steps:
                    step_order = step_data['order']
                    approver_id = step_data['approver_user_id']  # This is now an Approver UUID
                    
                    try:
                        approver = Approver.objects.get(id=approver_id)
                    except Approver.DoesNotExist:
                        # Rollback transaction
                        document.delete()
                        return Response(
                            {'error': f'Approver with ID {approver_id} does not exist.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    DocumentValidation.objects.create(
                        document=document,
                        step_order=step_order,
                        step_name=f"Step {step_order}",
                        assigned_approver=approver,
                        status='P'
                    )
                
                # Update document validation status
                document.update_validation_status()
            
            response_serializer = DocumentResponseSerializer(document)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return self.handle_exception(e)




class BaseDocumentValidationView(ErrorHandlerMixin, APIView):
    """
    Base class for document approval and rejection views.
    Handles common logic for both operations.
    """
    
    @transaction.atomic
    def post(self, request, document_id):
        serializer = ApproveRejectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        approver_id = serializer.validated_data['approver_user_id']
        reason = serializer.validated_data.get('reason', '')
        
        try:
            document = Document.objects.get(id=document_id)
            
            # Check if document is in pending status
            if document.validation_status != 'P':
                response_serializer = DocumentResponseSerializer(document)
                return Response(
                    {
                        'error': 'Document is no longer manageable.',
                        'document': response_serializer.data
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the approver
            approver = Approver.objects.get(id=approver_id)
            
            # Find the validation step assigned to this approver
            validation = document.get_pending_validation_for_approver(approver)
            
            if not validation:
                return Response(
                    {'error': 'No pending validation step assigned to this approver.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Process the validation (approve or reject)
            self._process_validation(document, validation, approver, reason)
            
            # Update document validation status
            document.update_validation_status()
            
            response_serializer = DocumentResponseSerializer(document)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)
    
    def _process_validation(self, document, validation, approver, reason):
        """
        Process the validation step. Must be implemented by subclasses.
        
        Args:
            document: Document instance
            validation: DocumentValidation instance
            approver: Approver instance
            reason: Reason string
        """
        raise NotImplementedError("Subclasses must implement _process_validation")


class DocumentApproveView(BaseDocumentValidationView):
    """
    API endpoint to approve a document validation step.
    POST /api/documents/{document_id}/approve/
    """
    
    def _process_validation(self, document, validation, approver, reason):
        """
        Approve this validation and all validations with lower or equal order.
        """
        approved_step_order = validation.step_order
        
        # Approve this validation and all validations with lower or equal order
        validations_to_approve = DocumentValidation.objects.filter(
            document=document,
            step_order__lte=approved_step_order,
            status='P'
        )
        
        for val in validations_to_approve:
            val.status = 'A'
            val.actor_approver = approver
            val.reason = reason
            val.action_date = timezone.now()
            val.save()


class DocumentRejectView(BaseDocumentValidationView):
    """
    API endpoint to reject a document validation step.
    POST /api/documents/{document_id}/reject/
    """
    
    def _process_validation(self, document, validation, approver, reason):
        """
        Reject the validation step.
        """
        validation.status = 'R'
        validation.actor_approver = approver
        validation.reason = reason
        validation.action_date = timezone.now()
        validation.save()
