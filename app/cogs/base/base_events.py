import datetime
import traceback
from typing import Any, List

import aiohttp
import discord
from discord import AsyncWebhookAdapter, Webhook
from discord.ext import commands, flags
from dotenv import load_dotenv

import config

from ... import errors
from ...classes.bot import Bot

IGNORED_ERRORS = [commands.CommandNotFound, errors.AllCommandsDisabled]
EXPECTED_ERRORS = [
    errors.ConversionError,
    errors.DoesNotExist,
    errors.AlreadyExists,
    errors.CommandDisabled,
    commands.MissingRequiredArgument,
    commands.ChannelNotFound,
    commands.RoleNotFound,
    commands.NotOwner,
    commands.CommandOnCooldown,
    discord.Forbidden,
    discord.InvalidArgument,
    flags.ArgumentParsingError,
]
UPTIME = config.UPTIME_WEBHOOK
ERROR = config.ERROR_WEBHOOK
GUILD = config.GUILD_WEBHOOK

load_dotenv()


async def uptime_log(content: str) -> None:
    if not UPTIME:
        return
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(
            UPTIME, adapter=AsyncWebhookAdapter(session)
        )
        await webhook.send(
            content, username="Starboard Uptime"
        )


async def error_log(content: str) -> None:
    if not ERROR:
        return
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(
            ERROR, adapter=AsyncWebhookAdapter(session)
        )
        await webhook.send(
            content, username="Starboard Errors"
        )


async def join_leave_log(embed: discord.Embed) -> None:
    if not GUILD:
        return
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(
            GUILD, adapter=AsyncWebhookAdapter(session)
        )
        await webhook.send(
            embed=embed, username="Starboard Guild Log"
        )


class BaseEvents(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.type_map = {
            "error": {"color": self.bot.error_color, "title": "Error"},
            "info": {"color": self.bot.theme_color, "title": "Info"},
        }

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        embed = discord.Embed(
            title=f"Joined **{guild.name}**",
            description=f"**{guild.member_count} members**",
            color=self.bot.theme_color,
        )
        embed.timestamp = datetime.datetime.utcnow()
        await join_leave_log(embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        embed = discord.Embed(
            title=f"Left **{guild.name}**",
            description=f"**{guild.member_count} members**",
            color=self.bot.dark_theme_color,
        )
        embed.timestamp = datetime.datetime.utcnow()
        await join_leave_log(embed)

    @commands.Cog.listener()
    async def on_log_error(
        self,
        title: str,
        error: Exception,
        args: List[Any] = [],
        kwargs: dict = {},
    ) -> None:
        p = commands.Paginator(prefix="```python")

        p.add_line(title)
        p.add_line(empty=True)
        p.add_line(f"{type(error)}: {error}")
        p.add_line(empty=True)
        p.add_line(f"Args: {args}")
        p.add_line(f"Kwargs: {kwargs}")
        p.add_line(empty=True)

        tb = traceback.format_tb(error.__traceback__)
        for line in tb:
            p.add_line(line=line)

        for page in p.pages:
            await error_log(page)

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id: int) -> None:
        self.bot.log.info(
            f"[Cluster#{self.bot.cluster_name}] Shard {shard_id} ready"
        )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.bot.log.info(f"[Cluster#{self.bot.cluster_name}] Ready")
        await uptime_log(
            f":green_circle: Cluster **{self.bot.cluster_name}** ready!"
        )
        try:
            self.bot.pipe.send(1)
        except BrokenPipeError:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.content.replace("!", "") == self.bot.user.mention:
            await message.channel.send("My prefix is `sb!`")
        else:
            await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, e: Exception
    ) -> None:
        try:
            e = e.original
        except AttributeError:
            pass
        if type(e) in IGNORED_ERRORS:
            return
        elif type(e) in EXPECTED_ERRORS:
            await ctx.send(e)
        elif type(e) == discord.errors.Forbidden:
            try:
                await ctx.message.author.send(
                    "I can't send messages in "
                    f"{ctx.message.channel.mention}, "
                    "or I'm missing the `Embed Links` "
                    "permission there."
                )
            except discord.Forbidden:
                pass
        else:
            embed = discord.Embed(
                title="Something's Not Right",
                description=(
                    "Something went wrong while "
                    "running this command. If the "
                    "problem persists, please report "
                    "this in the support server."
                ),
                color=self.bot.error_color,
            )
            tb = "".join(traceback.format_tb(e.__traceback__))
            full_tb = f"{e}\b" f"```{tb}```"
            if len(full_tb) > 1024:
                to_remove = (len(full_tb) - 1024) + 10
                full_tb = f"{e}\n```...{tb[to_remove:]}```"
            embed.add_field(name=e.__class__.__name__, value=full_tb)
            await ctx.send(embed=embed)

            self.bot.dispatch(
                "log_error", "Command Error", e, ctx.args, ctx.kwargs
            )

    @commands.Cog.listener()
    async def on_guild_log(
        self, message: str, log_type: str, guild: discord.Guild
    ) -> None:
        sql_guild = await self.bot.db.get_guild(guild.id)
        if sql_guild["log_channel"] is None:
            return
        log_channel = guild.get_channel(int(sql_guild["log_channel"]))
        if not log_channel:
            return

        embed = discord.Embed(
            title=self.type_map[log_type]["title"],
            description=message,
            color=self.type_map[log_type]["color"],
        )
        embed.timestamp = datetime.datetime.utcnow()
        await log_channel.send(embed=embed)


def setup(bot: Bot) -> None:
    bot.add_cog(BaseEvents(bot))

    @bot.before_invoke
    async def create_data(message: discord.Message) -> None:
        await bot.db.create_guild(message.guild.id)
        await bot.db.create_user(message.author.id, message.author.bot)
        await bot.db.create_member(message.author.id, message.guild.id)
