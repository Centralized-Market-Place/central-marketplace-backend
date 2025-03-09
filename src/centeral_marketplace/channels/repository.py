from centeral_marketplace.infrastructure.database import Database
from centeral_marketplace.channel.core import Channel
from injector import inject, singleton

@singleton
@inject
class ChannelRepository:
    def __init__(self, db: Database):
        self.db = db

    def find_all_by_dict(self, pagination, sort_by, sort_desc, criteria):
        query = self.db.channels.find(criteria)
        if sort_by:
            query = query.sort(sort_by, -1 if sort_desc else 1)
        query = query.skip((pagination.page - 1) * pagination.size).limit(pagination.size)
        return list(query)

    def count_all_by_dict(self, criteria):
        return self.db.channels.count_documents(criteria)

    def find_one(self, channel_id: str):
        return self.db.channels.find_one({"id": channel_id})
