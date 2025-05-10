from dataclasses import dataclass
import time
import cloudinary
import cloudinary.uploader
from injector import inject, singleton
from src.config import Config
from src.centeral_marketplace.files.core import FileType, SignedUrlResponse


@inject
@singleton
@dataclass
class FileService:
    config: Config
    
    def __post_init__(self):
        self.cloudinary_client = cloudinary.config(
            cloud_name=self.config.claudinary_cloud_name,
            api_key=self.config.claudinary_api_key,
            api_secret=self.config.claudinary_api_secret
        )
    
    def generate_signed_upload_url(self, file_type: FileType, folder: str = "uploads") -> SignedUrlResponse:
        timestamp = int(time.time())
        
        resource_type = self._get_resource_type(file_type)
        
        params = {
            "timestamp": timestamp,
            "folder": folder,
            "resource_type": resource_type
        }
        
        if resource_type == "image":
            params["allowed_formats"] = self._get_allowed_image_formats()
        
        signature = cloudinary.utils.api_sign_request(
            params_to_sign=params,
            api_secret=self.config.claudinary_api_secret
        )
        
        return SignedUrlResponse(
            signature=signature,
            timestamp=timestamp,
            cloud_name=self.config.claudinary_cloud_name,
            api_key=self.config.claudinary_api_key,
            folder=folder,
            resource_type=resource_type
        )
    
    def _get_resource_type(self, file_type: FileType) -> str:
        """Determine the Cloudinary resource type based on file extension"""
        if file_type == FileType.PDF:
            return "raw"
        return "image"
    
    def _get_allowed_image_formats(self) -> str:
        """Return comma-separated list of allowed image formats"""
        return "png,jpg,jpeg" 