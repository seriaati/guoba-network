from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "guild" (
    "id" BIGINT NOT NULL  PRIMARY KEY,
    "send_users" JSONB NOT NULL
);
COMMENT ON TABLE "guild" IS 'A Discord guild.';
CREATE TABLE IF NOT EXISTS "channel" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "type" VARCHAR(9) NOT NULL,
    "guild_id" BIGINT NOT NULL REFERENCES "guild" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_channel_channel_34a46c" UNIQUE ("channel_id", "type")
);
COMMENT ON COLUMN "channel"."type" IS 'NSFW_RECEIVE:  NSFW 接收站\nREGULAR_RECEIVE: 一般接收站\nSEND: 發送站';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
