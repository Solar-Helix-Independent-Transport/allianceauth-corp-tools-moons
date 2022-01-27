# Cog Stuff
from discord.embeds import Embed
from django_redis import get_redis_connection
from aadiscordbot.cogs.utils.decorators import sender_has_perm
from allianceauth.services.modules.discord.models import DiscordUser
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option

from discord import AutocompleteContext
# AA Contexts
import pprint
from corptools.models import CharacterAudit
from django.conf import settings
from django.db.models.query_utils import Q
from allianceauth.eveonline.models import EveCharacter
from moons.models import InvoiceRecord
import pinger

from pinger.tasks import get_settings, _get_cache_data_for_corp
from pinger.models import MutedStructure, PingerConfig
from corptools.models import EveLocation

from aadiscordbot import app_settings

import logging

logger = logging.getLogger(__name__)


class MoonsCog(commands.Cog):
    """
    All about Moons!
    """

    def __init__(self, bot):
        self.bot = bot

    pinger_commands = SlashCommandGroup(
        "moons", "Moon Module Commands", guild_ids=[int(settings.DISCORD_GUILD_ID)])

    def sender_has_moon_perm(self, ctx):
        id = ctx.author.id
        try:
            has_perm = DiscordUser.objects.get(
                uid=id).user.has_perm("moons.view_all")
            if has_perm:
                return True
            else:
                return False
        except Exception as e:
            return False

    @pinger_commands.command(name='print_stats', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    async def info_slash(self, ctx):
        """
        Print the Months Moning Stats!
        """

        if not self.sender_has_moon_perm(ctx):
            return await ctx.respond(f"You do not have permision to use this command.", ephemeral=True)

        await ctx.respond(f"Calculating the Moon Stats.", ephemeral=True)

        last_date = InvoiceRecord.get_last_invoice_date()
        e = Embed(title=f"Last Invoice {last_date}!")
        accounts_seen = 0
        locations = set()
        data = InvoiceRecord.generate_invoice_data()
        total_mined = 0
        total_taxed = 0
        # run known people
        for u, d in data['knowns'].items():
            try:
                total_mined += d['total_value']
                total_taxed += d['tax_value']

                accounts_seen += 1
                for l in d['locations']:
                    locations.add(l)
            except KeyError:
                pass  # probably wanna ping admin about it.

        for u, d in data['unknowns'].items():
            try:
                total_mined += d['totals_isk']
                total_taxed += d['tax_isk']
                for l in d['seen_at']:
                    locations.add(l)
            except KeyError:
                pass  # probably wanna ping admin about it.

        e.add_field(name="Known Members",
                    value=f"{accounts_seen}", inline=False)
        e.add_field(name="Unknown Characters",
                    value=f"{len(data['unknowns'])}", inline=False)
        e.add_field(name="Total Mined",
                    value=f"${total_mined:,}", inline=False)
        e.add_field(name="Total Tax", value=f"${total_taxed:,}", inline=False)
        locations = "\n ".join(list(locations))
        e.description = f'Locations tracked so far ({len(locations)})\n\n {locations}'

        await ctx.channel.send(embed=e)


def setup(bot):
    bot.add_cog(MoonsCog(bot))
