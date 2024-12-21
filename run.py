from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import sys

import discord
from loguru import logger

from wocardo.bot import WocardoBot
from wocardo.logging import InterceptHandler

env = os.getenv("ENV", "dev")
if env == "dev":
    logger.info("Running in development mode")
else:
    logger.info("Running in production mode")


async def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        msg = "Env variable 'DISCORD_TOKEN' is not set"
        raise ValueError(msg)

    async with WocardoBot() as bot:
        with contextlib.suppress(KeyboardInterrupt, asyncio.CancelledError):
            await bot.start(token)


if __name__ == "__main__":
    discord.VoiceClient.warn_nacl = False

    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if env == "dev" else "INFO")
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
    logger.add("logs/wocardo_network.log", rotation="1 day", retention="2 weeks", level="DEBUG")

    try:
        import uvloop  # pyright: ignore[reportMissingImports]
    except ImportError:
        asyncio.run(main())
    else:
        uvloop.run(main())
