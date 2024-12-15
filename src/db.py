from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

class MongoDB:

    client: AsyncIOMotorClient = None

    @classmethod
    def connect(cls):
        """
        Establish a connection to MongoDB.
        """
        if not cls.client:
            cls.client = AsyncIOMotorClient(settings.mongo_uri)
            print("MongoDB connection established.")

    @classmethod
    def close(cls):
        """
        Close the MongoDB connection.
        """
        if cls.client:
            cls.client.close()
            cls.client = None
            print("MongoDB connection closed.")

    @classmethod
    def get_database(cls, db_name: str = None):
        """
        Get a MongoDB database instance.

        :param db_name: Optional name of the database to connect to. Defaults to the value in settings.
        :return: AsyncIOMotorDatabase instance.
        """
        if not cls.client:
            raise ConnectionError("MongoDB client is not connected. Call `connect()` first.")
        return cls.client[db_name or settings.database_name]

