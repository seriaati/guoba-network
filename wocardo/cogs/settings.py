from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from wocardo.db.models import ChannelType, Guild
from wocardo.embeds import DefaultEmbed, ErrorEmbed

if TYPE_CHECKING:
    from wocardo.bot import WocardoBot
    from wocardo.types import Interaction


class Settings(commands.Cog):
    def __init__(self, bot: WocardoBot) -> None:
        self.bot = bot

    @app_commands.default_permissions()
    @app_commands.command(name="設置總覽", description="查看當前伺服器網路設置")
    async def show_settings(self, i: Interaction) -> None:
        if i.guild is None:
            return

        guild, _ = await Guild.get_or_create(id=i.guild.id)
        senders = await guild.get_senders()
        nsfw_receiver = await guild.get_receiver(nsfw=True)
        regular_receiver = await guild.get_receiver(nsfw=False)

        embed = DefaultEmbed(title="設置總覽")
        embed.add_field(
            name=ChannelType.REGULAR_RECEIVE.value,
            value=f"<#{regular_receiver}>" if regular_receiver else "尚未設置",
            inline=False,
        )
        embed.add_field(
            name=ChannelType.NSFW_RECEIVE.value,
            value=f"<#{nsfw_receiver}>" if nsfw_receiver else "尚未設置",
            inline=False,
        )
        embed.add_field(
            name=ChannelType.SEND.value,
            value=" ".join(f"<#{channel_id}>" for channel_id in senders) or "尚未設置",
            inline=False,
        )
        embed.add_field(
            name="發送人",
            value=" ".join(f"<@{user_id}>" for user_id in guild.send_users) or "尚未設置",
            inline=False,
        )

        await i.response.send_message(embed=embed)

    @app_commands.default_permissions()
    @app_commands.command(name="新增發送人", description="新增發送人")
    @app_commands.rename(user="發送人")
    @app_commands.describe(user="只有發送人發送的圖片才會被轉發到網路上的其他接收站")
    async def add_user(self, i: Interaction, user: discord.User) -> None:
        if i.guild is None:
            return

        guild, _ = await Guild.get_or_create(id=i.guild.id)
        await guild.add_send_user(user.id)

        await i.response.send_message(
            embed=DefaultEmbed(title="發送人新增成功", description=f"已新增 <@{user.id}>")
        )

    @app_commands.default_permissions()
    @app_commands.command(name="移除發送人", description="移除發送人")
    @app_commands.rename(user="發送人")
    @app_commands.describe(user="移除發送人後, 該使用者發送的圖片將不再被轉發到網路上的其他接收站")
    async def remove_user(self, i: Interaction, user: discord.User) -> None:
        if i.guild is None:
            return

        guild, _ = await Guild.get_or_create(id=i.guild.id)
        user_id = await guild.remove_send_user(user.id)

        if user_id is None:
            await i.response.send_message(
                embed=ErrorEmbed(
                    title="發送人移除失敗", description=f"此伺服器沒有將 <@{user.id}> 設置為發送人"
                ),
                ephemeral=True,
            )
            return
        await i.response.send_message(
            embed=DefaultEmbed(title="移除成功", description=f"已移除發送人 <@{user_id}>")
        )

    @app_commands.default_permissions()
    @app_commands.command(name="新增發送站", description="新增發送站")
    @app_commands.rename(channel="發送站")
    @app_commands.describe(channel="只有在發送站發送的圖片才會被轉發到網路上的其他接收站")
    async def set_sender(self, i: Interaction, channel: discord.TextChannel) -> None:
        if i.guild is None:
            return

        guild, _ = await Guild.get_or_create(id=i.guild.id)
        await guild.add_sender(channel.id)

        await i.response.send_message(
            embed=DefaultEmbed(title="發送站新增成功", description=f"已新增發送站 <#{channel.id}>")
        )

    @app_commands.default_permissions()
    @app_commands.command(name="移除發送站", description="移除發送站")
    @app_commands.rename(channel="發送站")
    @app_commands.describe(channel="移除發送站後, 該頻道發送的圖片將不再被轉發到網路上的其他接收站")
    async def remove_sender(self, i: Interaction, channel: discord.TextChannel) -> None:
        if i.guild is None:
            return

        guild, _ = await Guild.get_or_create(id=i.guild.id)
        channel_id = await guild.remove_sender(channel.id)

        if channel_id is None:
            await i.response.send_message(
                embed=ErrorEmbed(
                    title="發送站移除失敗",
                    description=f"此伺服器沒有將 <#{channel.id}> 設置為發送站",
                ),
                ephemeral=True,
            )
            return
        await i.response.send_message(
            embed=DefaultEmbed(title="移除成功", description=f"已移除發送站 <#{channel_id}>")
        )

    @app_commands.default_permissions()
    @app_commands.command(name="設置接收站", description="設置接收站")
    @app_commands.rename(channel="接收站")
    @app_commands.describe(channel="接收來自網路上其他發送站的圖片, 機器人會自動判斷接受站類別")
    async def set_receiver(self, i: Interaction, channel: discord.TextChannel) -> None:
        if i.guild is None:
            return

        guild, _ = await Guild.get_or_create(id=i.guild.id)
        channel_type = ChannelType.NSFW_RECEIVE if channel.nsfw else ChannelType.REGULAR_RECEIVE
        await guild.set_receiver(channel.id, nsfw=channel.nsfw)

        await i.response.send_message(
            embed=DefaultEmbed(
                title="接收站設置成功", description=f"已設置{channel_type.value} <#{channel.id}>"
            )
        )

    async def _remove_receiver(self, i: Interaction, channel_type: ChannelType) -> None:
        if i.guild is None:
            return

        guild, _ = await Guild.get_or_create(id=i.guild.id)
        channel_id = await guild.remove_receiver(nsfw=channel_type == ChannelType.NSFW_RECEIVE)

        if channel_id is None:
            await i.response.send_message(
                embed=ErrorEmbed(
                    title="接收站移除失敗", description=f"此伺服器沒有設置{channel_type.value}"
                ),
                ephemeral=True,
            )
            return
        await i.response.send_message(
            embed=DefaultEmbed(
                title="接收站移除成功", description=f"已移除{channel_type.value} <#{channel_id}>"
            )
        )

    @app_commands.default_permissions()
    @app_commands.command(name="移除一般接收站", description="將當前設置的一般接收站移除")
    async def remove_regular_receiver(self, i: Interaction) -> None:
        await self._remove_receiver(i, ChannelType.REGULAR_RECEIVE)

    @app_commands.default_permissions()
    @app_commands.command(name="移除nsfw接收站", description="將當前設置的 NSFW 接收站移除")
    async def remove_nsfw_receiver(self, i: Interaction) -> None:
        await self._remove_receiver(i, ChannelType.NSFW_RECEIVE)


async def setup(bot: WocardoBot) -> None:
    await bot.add_cog(Settings(bot))
