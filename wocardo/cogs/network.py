from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from wocardo.db.models import Guild

if TYPE_CHECKING:
    from wocardo.bot import WocardoBot


class Network(commands.Cog):
    def __init__(self, bot: WocardoBot) -> None:
        self.bot = bot

    async def _is_send_user(self, message: discord.Message, guild: Guild) -> bool:
        if message.guild is None:
            return False

        if message.webhook_id is not None:
            # Embed Fixer compatibility
            authors = await message.guild.query_members(
                message.author.display_name.removesuffix(" (Embed Fixer)")
            )
            if not authors:
                return False

            author = authors[0]
            if author.bot:
                return False
            author_id = authors[0].id
        else:
            author_id = message.author.id

        return author_id in guild.send_users

    async def _get_webhook(self, channel: discord.TextChannel) -> discord.Webhook:
        webhooks = await channel.webhooks()
        webhook_name = self.bot.user.name
        webhook = discord.utils.get(webhooks, name=webhook_name)
        if webhook is None:
            webhook = await channel.create_webhook(
                name=webhook_name, avatar=await self.bot.user.display_avatar.read()
            )

        return webhook

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        if (
            not message.attachments
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
        is_send_user = await self._is_send_user(message, guild)
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

            if isinstance(channel, discord.TextChannel):
                webhook = await self._get_webhook(channel)
                author_name = message.author.display_name.removesuffix(" (Embed Fixer)")
                await webhook.send(
                    content=message.content,
                    username=f"{author_name} (來自 {message.guild.name})",
                    avatar_url=message.author.display_avatar.url,
                    files=[
                        await attachment.to_file(spoiler=attachment.is_spoiler())
                        for attachment in message.attachments
                    ],
                )
            else:
                await channel.send(
                    content=f"(來自 {message.guild.name})\n{message.content}",
                    files=[
                        await attachment.to_file(spoiler=attachment.is_spoiler())
                        for attachment in message.attachments
                    ],
                )


async def setup(bot: WocardoBot) -> None:
    await bot.add_cog(Network(bot))
