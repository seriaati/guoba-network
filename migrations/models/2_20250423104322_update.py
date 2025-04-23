from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "messagelink" DROP COLUMN "guild_id";
        ALTER TABLE "messagelink" DROP COLUMN "author_id";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "messagelink" ADD "guild_id" BIGINT NOT NULL;
        ALTER TABLE "messagelink" ADD "author_id" BIGINT NOT NULL;"""
