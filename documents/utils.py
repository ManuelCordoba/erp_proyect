"""
Utility functions and helpers for the documents app.
"""
from rest_framework import status
from rest_framework.response import Response
from .models import Approver


def validate_approver_exists(approver_id):
    """
    Validate that an Approver exists.
    
    Args:
        approver_id: UUID of the approver to validate
        
    Returns:
        Approver instance if found
        
    Raises:
        Approver.DoesNotExist: If the approver doesn't exist
    """
    return Approver.objects.get(id=approver_id)

