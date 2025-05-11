from dataclasses import dataclass
import time
import cloudinary
import cloudinary.uploader
from injector import inject, singleton
from typing import Optional
import httpx
from config import Config
from centeral_marketplace.files.core import FileType, SignedUrlResponse


@inject
@singleton
@dataclass
class FileService:
    config: Config
    
    def __post_init__(self):
        self.cloudinary_client = cloudinary.config(
            cloud_name=self.config.cloudinary_cloud_name,
            api_key=self.config.cloudinary_api_key,
            api_secret=self.config.cloudinary_api_secret
        )
    
    def generate_signed_upload_url(self, file_type: FileType, folder: str = "uploads") -> SignedUrlResponse:
        timestamp = int(time.time())
        
        params = {
            "timestamp": timestamp,
            "folder": folder,
        }
        
        signature = cloudinary.utils.api_sign_request(
            params_to_sign=params,
            api_secret=self.config.cloudinary_api_secret
        )
        
        return SignedUrlResponse(
            signature=signature,
            timestamp=timestamp,
            cloud_name=self.config.cloudinary_cloud_name,
            api_key=self.config.cloudinary_api_key,
            folder=folder,
            resource_type=self._get_resource_type(file_type)
        )
    
    def _get_resource_type(self, file_type: FileType) -> str:
        if file_type == FileType.PDF:
            return "raw"
        return "image"
        
    def upload_from_url(self, url: str, folder: str = "channels") -> Optional[str]:
        try:
            # Download the file content
            with httpx.Client() as client:
                response = client.get(url)
                response.raise_for_status()
                
                # Upload to Cloudinary
                result = cloudinary.uploader.upload(
                    response.content,
                    folder=folder,
                    resource_type="auto"
                )
                
                return result.get("secure_url")
        except Exception as e:
            print(f"Error uploading file from URL: {e}")
            return None