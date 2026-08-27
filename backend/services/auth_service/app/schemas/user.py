"""
User Schemas - Profile related request/response validation

Pydantic models for:
- Get Profile
- Update Profile
"""

import re
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
from .auth import CleanResponse


# =============================================================================
# USER PROFILE
# =============================================================================

class UserProfile(BaseModel):
    """
    User profile data returned by API.
    
    Note: This is what we SEND to frontend, not what we store in DB.
    - email and phone are decrypted before sending
    - sensitive fields (password_hash) never included
    """
    
    user_id: str = Field(
        description="Unique user identifier"
    )
    
    user_name: str = Field(
        description="User's full name"
    )
    
    email: str = Field(
        description="User's email (decrypted)"
    )
    
    phone_number: str = Field(
        description="User's phone (decrypted)"
    )
    
    is_email_verified: bool = Field(
        description="Email verification status"
    )
    
    # Subscription info (null until subscription service assigns default)
    subscription_id: Optional[str] = Field(
        default=None,
        description="Current subscription ID (null for new users)"
    )
    
    subscription_name: Optional[str] = Field(
        default=None,
        description="Current subscription name (e.g., 'Free Tier', 'Premium')"
    )
    
    # Optional fields (may be null)
    address: Optional[str] = None
    pincode: Optional[str] = None
    preferences: Optional[dict[str, Any]] = None
    
    created_at: str = Field(
        description="Account creation timestamp (ISO format)"
    )


class GetProfileResponse(CleanResponse):
    """
    Response for GET /me
    
    Inherits from CleanResponse to auto-exclude None fields.
    """
    
    success: bool = True
    user: UserProfile


# =============================================================================
# UPDATE PROFILE
# =============================================================================

class UpdateProfileRequest(BaseModel):
    """
    Request body for profile update.
    
    All fields optional - only update what's provided.
    Email cannot be updated here (requires re-verification flow).
    """
    
    user_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="User's full name"
    )
    
    phone_number: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        description="Phone number with country code"
    )
    
    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User's address"
    )
    
    pincode: Optional[str] = Field(
        default=None,
        min_length=4,
        max_length=10,
        description="Postal/ZIP code"
    )
    
    preferences: Optional[dict[str, Any]] = Field(
        default=None,
        description="User preferences (theme, notifications, etc.)"
    )
    
    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    
    @field_validator('user_name')
    @classmethod
    def validate_user_name(cls, v: Optional[str]) -> Optional[str]:
        """Name can only contain letters and spaces."""
        if v is not None:
            v = v.strip()
            if not re.match(r'^[a-zA-Z\s]+$', v):
                raise ValueError("Name can only contain letters and spaces")
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Phone number format validation."""
        if v is not None:
            cleaned = re.sub(r'[\s\-]', '', v)
            if not re.match(r'^\+?\d{10,15}$', cleaned):
                raise ValueError("Invalid phone number format. Use: +919876543210")
            return cleaned
        return v
    
    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, v: Optional[str]) -> Optional[str]:
        """Pincode must be alphanumeric (supports international formats)."""
        if v is not None:
            v = v.strip().upper()
            if not re.match(r'^[A-Z0-9\s\-]+$', v):
                raise ValueError("Invalid pincode format")
        return v
    
    @field_validator('preferences')
    @classmethod
    def validate_preferences(cls, v: Optional[dict]) -> Optional[dict]:
        """
        Validate preferences structure.
        
        Expected format:
        {
            "theme": "dark" | "light",
            "notifications": {
                "email": true/false,
                "push": true/false
            },
            "language": "en" | "hi" | ...
        }
        """
        if v is not None:
            allowed_keys = {'theme', 'notifications', 'language', 'timezone'}
            invalid_keys = set(v.keys()) - allowed_keys
            if invalid_keys:
                raise ValueError(f"Invalid preference keys: {invalid_keys}")
            
            # Validate theme
            if 'theme' in v and v['theme'] not in ['dark', 'light', 'system']:
                raise ValueError("Theme must be 'dark', 'light', or 'system'")
        
        return v


class UpdateProfileResponse(BaseModel):
    """Response after successful profile update."""
    
    success: bool = True
    message: str = "Profile updated successfully"
    user: UserProfile
