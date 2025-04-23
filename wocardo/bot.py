from __future__ import annotations

from pathlib import Path

import discord
from discord.ext import commands
from loguru import logger
from tortoise import Tortoise

from wocardo.command_tree import CommandTree
from wocardo.db.config import TORTOISE_ORM


class WocardoBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned,
            case_insensitive=True,
            intents=intents,
            help_command=None,
            mex_messages=None,
            chunk_guilds_at_startup=False,
            member_cache_flags=discord.MemberCacheFlags.none(),
            allowed_contexts=discord.app_commands.AppCommandContext(
                guild=True, dm_channel=False, private_channel=False
            ),
            allowed_mentions=discord.AllowedMentions.none(),
            tree_cls=CommandTree,
        )
        self.user: discord.ClientUser

    async def setup_hook(self) -> None:
        logger.info("Initializing database")
        await Tortoise.init(TORTOISE_ORM)

        for filepath in Path("wocardo/cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.load_extension(f"wocardo.cogs.{cog_name}")
                logger.info(f"Loaded cog {cog_name!r}")
            except Exception:
                logger.exception(f"Failed to load cog {cog_name!r}")

        await self.load_extension("jishaku")

    async def close(self) -> None:
        await super().close()
        await Tortoise.close_connections()
