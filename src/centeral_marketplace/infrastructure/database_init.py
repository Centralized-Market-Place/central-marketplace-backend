from pymongo import ASCENDING, DESCENDING, MongoClient
from config import Config
from typing import Dict
from dataclasses import dataclass
from pymongo.database import Database
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseInitializer:
    config: Config
    _initialized: Dict[str, bool] = None

    def __post_init__(self):
        self._initialized = {}
        self._client = MongoClient(self.config.mongo_uri)
        self._db: Database = self._client[self.config.database_name]

    def initialize_product_indexes(self):
        if self._initialized.get("products"):
            return
        
        collection = self._db["structured_products"]
        
        collection.create_index([
            ("name", "text"),
            ("description", "text")
        ], name="products_text_search")
        
        collection.create_index([
            ("channel_id", ASCENDING),
            ("created_at", DESCENDING)
        ], name="products_channel_created")
        
        collection.create_index([("created_at", DESCENDING)], name="products_created_at")
        collection.create_index([("date", DESCENDING)], name="products_date")
        collection.create_index([("updated_at", DESCENDING)], name="products_updated_at")
        collection.create_index([("price", ASCENDING)], name="products_price")
        
        logger.info("Product indexes initialized successfully")
        self._initialized["products"] = True

    def initialize_reaction_indexes(self):
        if self._initialized.get("reactions"):
            return
            
        collection = self._db["reactions"]
        
        collection.create_index([
            ("target_id", ASCENDING),
            ("user_id", ASCENDING),
            ("target_type", ASCENDING)
        ], unique=True, name="reactions_unique_user_target")
        
        collection.create_index([("user_id", ASCENDING)], name="reactions_user")
        collection.create_index([("target_id", ASCENDING)], name="reactions_target")
        collection.create_index([("created_at", DESCENDING)], name="reactions_created_at")
        
        logger.info("Reaction indexes initialized successfully")
        self._initialized["reactions"] = True

    def initialize_bookmark_indexes(self):
        if self._initialized.get("bookmarks"):
            return
            
        collection = self._db["bookmarks"]
        
        collection.create_index([
            ("user_id", ASCENDING),
            ("product_id", ASCENDING),
            ("created_at", DESCENDING)
        ], unique=True, name="bookmarks_unique_user_product")
        
        collection.create_index([("product_id", ASCENDING)], name="bookmarks_product")
        collection.create_index([
            ("user_id", ASCENDING),
            ("created_at", DESCENDING)
        ], name="bookmarks_user_created")
        
        logger.info("Bookmark indexes initialized successfully")
        self._initialized["bookmarks"] = True

    def initialize_user_indexes(self):
        if self._initialized.get("users"):
            return
            
        collection = self._db["users"]
        
        collection.create_index([("email", ASCENDING)], unique=True, name="users_email")
        collection.create_index([("created_at", DESCENDING)], name="users_created_at")
        logger.info("User indexes initialized successfully")
        self._initialized["users"] = True

    def initialize_channel_indexes(self):
        if self._initialized.get("channels"):
            return
            
        collection = self._db["channels"]
        
        collection.create_index([
            ("name", "text"),
            ("description", "text")
        ], name="channels_text_search")
        
        collection.create_index([("created_at", DESCENDING)], name="channels_created_at")
        logger.info("Channel indexes initialized successfully")
        self._initialized["channels"] = True

    def initialize_all(self):
        try:
            self.initialize_product_indexes()
            self.initialize_reaction_indexes()
            self.initialize_bookmark_indexes()
            self.initialize_user_indexes()
            self.initialize_channel_indexes()
            logger.info("All database indexes initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database indexes: {e}")
            raise

    def cleanup(self):
        if self._client:
            self._client.close()
            logger.info("Database connections closed") 