from __future__ import annotations

import re
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from loguru import logger

from wocardo.db.models import Guild, MessageLink

if TYPE_CHECKING:
    from wocardo.bot import WocardoBot

FILE_TOO_LARGE_RETCODE = 40005
MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".mkv"}
NAME_PATTERN = r"^(.*?)\s+\(來自:.*\)$"


class Network(commands.Cog):
    def __init__(self, bot: WocardoBot) -> None:
        self.bot = bot

    @staticmethod
    def _extract_author_name(name: str) -> str | None:
        match = re.search(NAME_PATTERN, name)
        if match:
            return match.group(1)
        return None

    async def _is_send_user(
        self, message: discord.Message, guild: Guild
    ) -> tuple[discord.Member | None, bool]:
        author = None
        if message.guild is None:
            return author, False

        if message.webhook_id is not None:
            # Embed Fixer compatibility
            authors = await message.guild.query_members(
                message.author.display_name.removesuffix(" (Embed Fixer)")
            )
            if not authors:
                return author, False

            author = authors[0]
            if author.bot:
                return author, False
            author_id = authors[0].id
        else:
            author_id = message.author.id

        return author, author_id in guild.send_users

    async def _get_webhook(self, channel: discord.TextChannel) -> discord.Webhook:
        webhooks = await channel.webhooks()
        webhook_name = self.bot.user.name
        webhook = discord.utils.get(webhooks, name=webhook_name)
        if webhook is None:
            webhook = await channel.create_webhook(
                name=webhook_name, avatar=await self.bot.user.display_avatar.read()
            )

        return webhook

    async def _send_message(
        self,
        *,
        message: discord.Message,
        author: discord.Member | discord.User | None,
        guild: discord.Guild,
        channel: discord.VoiceChannel | discord.TextChannel | discord.StageChannel | discord.Thread,
        files: list[discord.File],
    ) -> discord.Message:
        if isinstance(channel, discord.TextChannel):
            webhook = await self._get_webhook(channel)
            author_name = message.author.name.removesuffix(" (Embed Fixer)")
            author = author or message.author
            return await webhook.send(
                content=message.content,
                username=f"{author_name} (來自:{guild.name})",
                avatar_url=author.display_avatar.url,
                files=files,
                wait=True,
            )

        return await channel.send(content=f"(來自:{guild.name})\n{message.content}", files=files)

    @commands.Cog.listener("on_message")
    async def forward_medias(self, message: discord.Message) -> None:  # noqa: C901
        if (
            (not message.attachments and not any(ext in message.content for ext in MEDIA_EXTS))
            or message.guild is None
            or isinstance(
                message.channel,
                discord.DMChannel | discord.GroupChannel | discord.PartialMessageable,
            )
            or (message.author.bot and message.webhook_id is None)
        ):
            return

        guild = await Guild.get_or_none(id=message.guild.id)
        if guild is None:
            return

        # Is sender?
        senders = await guild.get_senders()
        if message.channel.id not in senders:
            return

        # Is send user?
        author, is_send_user = await self._is_send_user(message, guild)
        if not is_send_user:
            return

        # Send to other guilds
        is_nsfw = message.channel.is_nsfw()
        guilds = await Guild.all()

        for guild in guilds:
            if guild.id == message.guild.id:
                continue

            receiver = await guild.get_receiver(nsfw=is_nsfw)
            if receiver is None:
                continue

            dc_guild = self.bot.get_guild(guild.id) or await self.bot.fetch_guild(guild.id)
            channel = dc_guild.get_channel(receiver) or await dc_guild.fetch_channel(receiver)
            if isinstance(channel, discord.ForumChannel | discord.CategoryChannel):
                continue

            files = [
                await attachment.to_file(spoiler=attachment.is_spoiler())
                for attachment in message.attachments
            ]
            try:
                sent_message = await self._send_message(
                    message=message,
                    author=author,
                    guild=message.guild,
                    channel=channel,
                    files=files,
                )
            except discord.HTTPException as e:
                if e.code != FILE_TOO_LARGE_RETCODE:
                    raise

                message.content += f"\n{'\n'.join(a.url for a in message.attachments)}"
                sent_message = await self._send_message(
                    message=message, author=author, guild=message.guild, channel=channel, files=[]
                )

            await sent_message.add_reaction("❌")

            await MessageLink.create(
                id=sent_message.id,
                author_id=message.author.id,
                channel_id=message.channel.id,
                guild_id=guild.id,
                source_id=message.id,
            )

    @commands.Cog.listener("on_raw_message_delete")
    async def delete_message_links(self, payload: discord.RawMessageDeleteEvent) -> None:
        message_id = payload.message_id
        logger.info(f"Noticed message {message_id} deleted")

        message_links = await MessageLink.filter(source_id=message_id)
        logger.info(f"Found {len(message_links)} message links")

        for message_link in message_links:
            try:
                channel = self.bot.get_partial_messageable(message_link.channel_id)
                await channel.get_partial_message(message_link.id).delete()
            except discord.HTTPException:
                pass
            else:
                await message_link.delete()

    @commands.Cog.listener("on_raw_reaction_add")
    async def delete_message_on_reaction(self, reaction: discord.RawReactionActionEvent) -> None:
        if str(reaction.emoji) != "❌":
            return

        message = await self.bot.get_partial_messageable(reaction.channel_id).fetch_message(
            reaction.message_id
        )
        author = await self.bot.fetch_user(reaction.user_id)
        author_name = self._extract_author_name(message.author.name)

        if author_name is None or author_name != author.name:
            return

        await message.delete()


async def setup(bot: WocardoBot) -> None:
    await bot.add_cog(Network(bot))
