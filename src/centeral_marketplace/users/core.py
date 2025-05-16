from datetime import datetime
from enum import Enum
from typing import List, Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from centeral_marketplace.sellers.core import SellerInfo
from pydantic import  BaseModel, EmailStr, Field
from core import PyObjectId


class Role(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    SELLER = "SELLER"
    SUPER_ADMIN = "SUPER_ADMIN"


class TelegramData(BaseModel):
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: datetime = Field(default_factory=datetime.utcnow)


class PersonalInfo(BaseModel):
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    bio: Optional[str] = None




class ContactInfo(BaseModel):
    phone_number: Optional[str] = None
    alternative_email: Optional[EmailStr] = None
    preferred_contact_method: str = "email"


class LocationInfo(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    timezone: Optional[str] = None



class CommunicationPreferences(BaseModel):
    language: str = "en"
    email_notifications: bool = True
    sms_notifications: bool = False
    marketing_emails: bool = False
    notification_frequency: str = "daily"


class PrivacySettings(BaseModel):
    profile_visibility: str = "public"
    show_email: bool = False
    show_phone: bool = False
    show_location: bool = True
    show_activity: bool = True



class VerificationStatus(BaseModel):
    email_verified: bool = False
    phone_verified: bool = False
    identity_verified: bool = False
    verification_method: Optional[str] = None
    verification_date: Optional[datetime] = None


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class User(UserBase, MongoBaseModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    contact_info: ContactInfo = Field(default_factory=lambda: ContactInfo(email=""))
    location_info: LocationInfo = Field(default_factory=LocationInfo)

    communication_preferences: CommunicationPreferences = Field(
        default_factory=CommunicationPreferences
    )
    privacy_settings: PrivacySettings = Field(default_factory=PrivacySettings)

    verification_status: VerificationStatus = Field(default_factory=VerificationStatus)
    password_hash: str
    role: Role = Role.USER
    profile_picture_url: Optional[str] = None
    is_verified: bool = False
    telegram: Optional[TelegramData] = None
    seller_infos: List[SellerInfo] = []
    last_login: Optional[datetime] = None
    last_active: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

    def is_profile_complete(self) -> bool:
        required_fields = [
            self.first_name,
            self.last_name,
            self.contact_info.phone_number,
            self.location_info.country,
            self.location_info.city,
        ]
        return all(field is not None for field in required_fields)

    def get_completion_percentage(self) -> float:
        total_fields = 13
        completed_fields = sum(
            1
            for field in [
                self.first_name,
                self.last_name,
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
                self.verification_status.phone_verified,
            ]
            if field is not None
        )

        return (completed_fields / total_fields) * 100


class UserPublic(UserBase):
    id: PyObjectId
    role: Role
    is_verified: bool
    profile_picture_url: Optional[str] = None
    last_login: Optional[datetime] = None
    telegram: Optional[TelegramData] = None
    seller_infos: List[SellerInfo] = []
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime] = None
    personal_info: Optional[PersonalInfo] = None
    contact_info: Optional[ContactInfo] = None
    location_info: Optional[LocationInfo] = None
    communication_preferences: Optional[CommunicationPreferences] = None
    privacy_settings: Optional[PrivacySettings] = None
    verification_status: Optional[VerificationStatus] = None
    

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class AuthResponse(BaseModel):
    token: str
    user: User


class UpdateUser(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    personal_info: Optional[PersonalInfo] = None
    contact_info: Optional[ContactInfo] = None
    location_info: Optional[LocationInfo] = None
    communication_preferences: Optional[CommunicationPreferences] = None
    privacy_settings: Optional[PrivacySettings] = None


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    personal_info: Optional[PersonalInfo] = None
    contact_info: Optional[ContactInfo] = None
    location_info: Optional[LocationInfo] = None
    communication_preferences: Optional[CommunicationPreferences] = None
    privacy_settings: Optional[PrivacySettings] = None


class TelegramLogin(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
