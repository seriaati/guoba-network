# pyright: reportAssignmentType=false

from __future__ import annotations

from enum import StrEnum

from tortoise import fields
from tortoise.models import Model


class ChannelType(StrEnum):
    NSFW_RECEIVE = " NSFW 接收站"
    REGULAR_RECEIVE = "一般接收站"
    SEND = "發送站"


class BaseModel(Model):
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(f'{field}={getattr(self, field)!r}' for field in self._meta.db_fields if hasattr(self, field))})"  # noqa: E501

    def __repr__(self) -> str:
        return str(self)

    class Meta:
        abstract = True


class Channel(BaseModel):
    channel_id = fields.BigIntField()
    guild: fields.ForeignKeyRelation[Guild] = fields.ForeignKeyField(
        "models.Guild", related_name="channels"
    )
    type = fields.CharEnumField(ChannelType)

    class Meta:
        unique_together = ("channel_id", "type")


class Guild(BaseModel):
    """A Discord guild.

    Can only have 1 regular receiver and 1 NSFW receiver at the same time.
    Can have multiple regular senders and multiple NSFW senders.
    """

    id = fields.BigIntField(pk=True, generated=False)
    send_users: fields.Field[list[int]] = fields.JSONField(default=[])

    async def remove_receiver(self, *, nsfw: bool) -> int | None:
        channel = await Channel.get_or_none(
            guild_id=self.id, type=ChannelType.NSFW_RECEIVE if nsfw else ChannelType.REGULAR_RECEIVE
        )
        if channel is None:
            return None
        await channel.delete()
        return channel.channel_id

    async def set_receiver(self, channel_id: int, *, nsfw: bool) -> None:
        await self.remove_receiver(nsfw=nsfw)
        await Channel.get_or_create(
            guild_id=self.id,
            channel_id=channel_id,
            type=ChannelType.NSFW_RECEIVE if nsfw else ChannelType.REGULAR_RECEIVE,
        )

    async def get_receiver(self, *, nsfw: bool) -> int | None:
        channel = await Channel.get_or_none(
            guild_id=self.id, type=ChannelType.NSFW_RECEIVE if nsfw else ChannelType.REGULAR_RECEIVE
        )
        return channel.channel_id if channel else None

    async def add_sender(self, channel_id: int) -> None:
        await Channel.get_or_create(guild_id=self.id, channel_id=channel_id, type=ChannelType.SEND)

    async def remove_sender(self, channel_id: int) -> int | None:
        channel = await Channel.get_or_none(
            guild_id=self.id, channel_id=channel_id, type=ChannelType.SEND
        )
        if channel is None:
            return None
        await channel.delete()
        return channel.channel_id

    async def get_senders(self) -> list[int]:
        return [
            channel.channel_id
            for channel in await Channel.filter(guild_id=self.id, type=ChannelType.SEND)
        ]

    async def add_send_user(self, user_id: int) -> None:
        self.send_users.append(user_id)
        self.send_users = list(set(self.send_users))
        await self.save(update_fields=("send_users",))

    async def remove_send_user(self, user_id: int) -> int | None:
        if user_id not in self.send_users:
            return None

        self.send_users.remove(user_id)
        await self.save(update_fields=("send_users",))
        return user_id
