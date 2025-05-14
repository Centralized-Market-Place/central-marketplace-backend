import logging
from typing import Any, Dict, Optional
import httpx
from injector import inject, singleton
from pydantic import BaseModel, Field

from config import Config
from centeral_marketplace.channels.core import Channel
from centeral_marketplace.files.service import FileService

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class ChatAdminResponse(BaseModel):
    ok: bool
    result: list = Field(default_factory=list)


class ChatMember(BaseModel):
    user: Dict[str, Any]
    status: str
    is_anonymous: bool = False
    can_manage_chat: bool = False
    can_change_info: bool = False
    can_post_messages: bool = False
    can_edit_messages: bool = False
    can_delete_messages: bool = False
    can_invite_users: bool = False
    can_restrict_members: bool = False
    can_promote_members: bool = False
    can_manage_video_chats: bool = False
    can_manage_topics: bool = False


class BotAddedResponse(BaseModel):
    ok: bool
    result: Optional[Dict[str, Any]] = None


class TelegramChannelResponse(BaseModel):
    ok: bool
    result: Optional[Dict[str, Any]] = None
    


@singleton
class TelegramService:

    @inject
    def __init__(self, config: Config, file_service: FileService):
        self.config = config
        self.file_service = file_service
        self.base_url = f"https://api.telegram.org/bot{config.telegram_bot_token}"

    def get_chat_administrators(self, chat_id: str) -> ChatAdminResponse:
        if not chat_id.startswith("@"):
            chat_id = "@" + chat_id

        url = f"{self.base_url}/getChatAdministrators"
        
        try:
            with httpx.Client() as client:
                response = client.get(url, params={"chat_id": chat_id})
                response.raise_for_status()
                return ChatAdminResponse(**response.json())
        except Exception as e:
            logger.error(f"Error getting chat administrators: {e}")
            return ChatAdminResponse(ok=False)

    def is_bot_admin(self, chat_id: str) -> bool:
        response = self.get_chat_administrators(chat_id)
        if not response.ok:
            return False
        
        for admin in response.result:
            chat_member = ChatMember(**admin)
            if chat_member.user.get("username") == self.config.telegram_bot_username:
                return chat_member.status == "administrator"
        
        return False

    def verify_chat_exists(self, chat_id: str) -> bool:
        if not chat_id.isdigit() and not chat_id.startswith("@"):
            chat_id = "@" + chat_id

        url = f"{self.base_url}/getChat"
        
        try:
            with httpx.Client() as client:
                response = client.get(url, params={"chat_id": chat_id})
                return response.status_code == 200
        except Exception:
            return False

    def get_bot_info(self) -> Dict[str, Any]:
        url = f"{self.base_url}/getMe"
        
        try:
            with httpx.Client() as client:
                response = client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {"ok": False}
            
    def verify_channel_ownership(self, user_telegram_id: int, channel_id: str) -> bool:
        response = self.get_chat_administrators(channel_id)
        if not response.ok:
            return False
            
        for admin in response.result:
            chat_member = ChatMember(**admin)
            if (chat_member.status == "creator" or chat_member.status == "administrator") and chat_member.user.get("id") == user_telegram_id:
                return True
                
        return False
        
    def get_channel_info(self, chat_id: str) -> Channel:
        telegram_id = chat_id   
        if not chat_id.startswith("@"):
            telegram_id = "@" + chat_id

        url = f"{self.base_url}/getChat"
        
        try:
            with httpx.Client() as client:
                response = client.get(url, params={"chat_id": telegram_id})
                response.raise_for_status()
                chat_data = TelegramChannelResponse.model_validate(response.json())
                
                if not chat_data.ok or not chat_data.result:
                    logger.error(f"Error getting channel info: {chat_data}")
                    return None
                    
                result = chat_data.result

                member_count = 0
                try:
                    member_count_response = client.get(
                        f"{self.base_url}/getChatMemberCount", 
                        params={"chat_id": telegram_id}
                    )
                    if member_count_response.status_code == 200:
                        member_count_data = member_count_response.json()
                        if member_count_data.get("ok"):
                            member_count = member_count_data.get("result", 0)
                except Exception as e:
                    logger.error(f"Error getting member count: {e}")
                
                channel = Channel(
                    title=result.get("title", ""),
                    username=chat_id,
                    description=result.get("description", ""),
                    thumbnail_url="",
                    participants=member_count,
                    verified=False,
                    restricted=result.get("is_restricted", False),
                    scam=result.get("is_scam", False),
                    has_geo=result.get("has_protected_content", False),
                    has_link=result.get("invite_link") is not None,
                    broadcast=result.get("type") == "channel",
                    telegram_id=result.get("id") if result.get("id") else 0
                )
                
                if result.get("photo"):
                    file_id = result.get("photo", {}).get("big_file_id")
                    if file_id:
                        photo_url = self.get_file_url(file_id)
                        if photo_url:
                            cloudinary_url = self.file_service.upload_from_url(
                                photo_url, 
                                folder=f"channels/{chat_id}"
                            )
                            if cloudinary_url:
                                channel.thumbnail_url = cloudinary_url
                
                return channel
                
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
            
    def get_file_url(self, file_id: str) -> Optional[str]:
        try:
            with httpx.Client() as client:
                file_info_response = client.get(
                    f"{self.base_url}/getFile", 
                    params={"file_id": file_id}
                )
                file_info_response.raise_for_status()
                file_info = file_info_response.json()
                
                if not file_info.get("ok"):
                    return None
                    
                file_path = file_info.get("result", {}).get("file_path")
                if not file_path:
                    return None

                return f"https://api.telegram.org/file/bot{self.config.telegram_bot_token}/{file_path}"
                
        except Exception as e:
            logger.error(f"Error getting file URL: {e}")
            return None 