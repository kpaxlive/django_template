"""
Standardized API response utilities.
"""
from rest_framework import status


class ResponseCodes:
    """Standard response codes for API."""
    
    # Success codes
    SUCCESS = "SUCCESS"
    CREATED = "CREATED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"
    
    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    
    # OAuth errors
    OAUTH_ERROR = "OAUTH_ERROR"
    GOOGLE_AUTH_FAILED = "GOOGLE_AUTH_FAILED"
    APPLE_AUTH_FAILED = "APPLE_AUTH_FAILED"
    
    # General errors
    SERVER_ERROR = "SERVER_ERROR"
    NOT_FOUND = "NOT_FOUND"


def success_response(message, data=None, code=ResponseCodes.SUCCESS, http_status=status.HTTP_200_OK):
    """
    Create a standardized success response.
    
    Args:
        message (str): Success message
        data (dict, optional): Response data
        code (str): Response code
        http_status (int): HTTP status code
        
    Returns:
        tuple: (response_dict, http_status)
    """
    response = {
        "success": True,
        "code": code,
        "message": message,
    }
    
    if data is not None:
        response["data"] = data
    
    return response, http_status


def error_response(error, code=ResponseCodes.VALIDATION_ERROR, http_status=status.HTTP_400_BAD_REQUEST):
    """
    Create a standardized error response.
    
    Args:
        error (str): Error message
        code (str): Error code
        http_status (int): HTTP status code
        
    Returns:
        tuple: (response_dict, http_status)
    """
    response = {
        "success": False,
        "code": code,
        "error": error,
    }
    
    return response, http_status

