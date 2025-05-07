import logging
from typing import Any, Dict, Optional
import httpx
from injector import inject, singleton
from pydantic import BaseModel, Field

from config import Config

logger = logging.getLogger(__name__)


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


@singleton
class TelegramService:

    @inject
    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"https://api.telegram.org/bot{config.telegram_bot_token}"

    def get_chat_administrators(self, chat_id: str) -> ChatAdminResponse:
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