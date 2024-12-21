from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from discord import NotFound, app_commands

from wocardo.embeds import ErrorEmbed

if TYPE_CHECKING:
    from wocardo.types import Interaction


class CommandTree(app_commands.CommandTree):
    async def on_error(self, i: Interaction, e: app_commands.AppCommandError) -> None:
        error = e.original if isinstance(e, app_commands.errors.CommandInvokeError) else e
        if isinstance(error, app_commands.CheckFailure):
            return

        embed = ErrorEmbed(title="錯誤", description=str(error))

        with contextlib.suppress(NotFound):
            if i.response.is_done():
                await i.followup.send(embed=embed, ephemeral=True)
            else:
                await i.response.send_message(embed=embed, ephemeral=True)
