from __future__ import annotations

import discord


class DefaultEmbed(discord.Embed):
    def __init__(self, *, title: str | None = None, description: str | None = None) -> None:
        super().__init__(
            title=title, description=description, color=discord.Color.from_rgb(150, 111, 72)
        )


class ErrorEmbed(discord.Embed):
    def __init__(self, *, title: str | None = None, description: str | None = None) -> None:
        super().__init__(
            title=title, description=description, color=discord.Color.from_rgb(224, 63, 51)
        )
