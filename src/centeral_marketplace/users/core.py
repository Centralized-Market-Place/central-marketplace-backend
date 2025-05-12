from datetime import datetime
from enum import Enum
from typing import Optional, Dict
from bson import ObjectId
from centeral_marketplace.sellers.core import SellerInfo
from pydantic import AliasChoices, BaseModel, EmailStr, Field
from core import PyObjectId


class Role(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    SELLER = "SELLER"


class TelegramData(BaseModel):
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: datetime = Field(default_factory=datetime.utcnow)


class PersonalInfo(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class ContactInfo(BaseModel):
    phone_number: Optional[str] = None
    alternative_email: Optional[EmailStr] = None
    preferred_contact_method: str = "email"  

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class LocationInfo(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    timezone: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class CommunicationPreferences(BaseModel):
    language: str = "en"
    email_notifications: bool = True
    sms_notifications: bool = False
    marketing_emails: bool = False
    notification_frequency: str = "daily"  

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class PrivacySettings(BaseModel):
    profile_visibility: str = "public"  
    show_email: bool = False
    show_phone: bool = False
    show_location: bool = True
    show_activity: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class VerificationStatus(BaseModel):
    email_verified: bool = False
    phone_verified: bool = False
    identity_verified: bool = False
    verification_method: Optional[str] = None
    verification_date: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class UserBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    personal_info: Optional[PersonalInfo] = None
    contact_info: Optional[ContactInfo] = None
    location_info: Optional[LocationInfo] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class User(UserBase):
    id: PyObjectId = Field(
        default_factory=ObjectId,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
   
    personal_info: PersonalInfo = Field(default_factory=lambda: PersonalInfo(
        first_name="",
        last_name=""
    ))
    contact_info: ContactInfo = Field(default_factory=lambda: ContactInfo(
        email=""
    ))
    location_info: LocationInfo = Field(default_factory=LocationInfo)
    
    
    communication_preferences: CommunicationPreferences = Field(default_factory=CommunicationPreferences)
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)
    
    
    verification_status: VerificationStatus = Field(default_factory=VerificationStatus)
    password_hash: str
    role: Role = Role.USER
    is_verified: bool = False
    
    seller_info: Optional[SellerInfo] = None
    
    telegram: Optional[TelegramData] = None
    
    last_login: Optional[datetime] = None
    last_active: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

    def is_profile_complete(self) -> bool:
        """Check if the profile has all required information"""
        required_fields = [
            self.personal_info.first_name,
            self.personal_info.last_name,
            self.contact_info.phone_number,
            self.location_info.country,
            self.location_info.city
        ]
        return all(field is not None for field in required_fields)

    def get_completion_percentage(self) -> float:
        """Calculate profile completion percentage"""
        total_fields = 15  
        completed_fields = sum(1 for field in [
            self.personal_info.first_name,
            self.personal_info.last_name,
            self.personal_info.date_of_birth,
            self.personal_info.gender,
            self.personal_info.profile_picture,
            self.contact_info.phone_number,
            self.location_info.country,
            self.location_info.city,
            self.location_info.address,
            self.location_info.postal_code,
            self.telegram,
            self.personal_info.bio,
            self.verification_status.email_verified,
            self.verification_status.phone_verified
        ] if field is not None)
        
        return (completed_fields / total_fields) * 100


class UserPublic(UserBase):
    id: PyObjectId = Field(alias="_id")
    role: Role
    is_verified: bool
    profile_picture: Optional[str] = None
    last_login: Optional[datetime] = None
    telegram: Optional[TelegramData] = None
    seller_info: Optional[SellerInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class AuthResponse(BaseModel):
    token: str
    user: User


class TelegramLogin(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
