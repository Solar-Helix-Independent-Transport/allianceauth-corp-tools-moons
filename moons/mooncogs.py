# Cog Stuff
from typing import Optional
from corptools.models import CorporationAudit, Structure
from discord.embeds import Embed
from allianceauth.services.modules.discord.models import DiscordUser
from discord.ext import commands
from discord.commands import SlashCommandGroup

# AA Contexts
import pprint
from django.conf import settings
from django.utils import timezone
from moons.models import InvoiceRecord, MoonFrack

from moons import app_settings

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

    def sender_has_corp_moon_perm(self, ctx):
        id = ctx.author.id
        try:
            has_perm = DiscordUser.objects.get(
                uid=id).user.has_perm("moons.view_corp")
            if has_perm:
                return True
            else:
                return False
        except Exception as e:
            return False

    @pinger_commands.command(name='print_stats', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    async def info_slash(self, ctx):
        """
        Print the Uninvocied Mining Stats!
        """

        if not self.sender_has_moon_perm(ctx):
            return await ctx.respond(f"You do not have permision to use this command.", ephemeral=True)

        await ctx.respond(f"Calculating the Moon Stats.")

        last_date = InvoiceRecord.get_last_invoice_date()
        date_str = last_date.strftime('%Y/%m/%d')
        e = Embed(title=f"Last Invoice {date_str}")
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
        e.description = f'Locations tracked so far ({len(list(locations))})\n\n {locations}'

        await ctx.channel.send(embed=e)

    @pinger_commands.command(name='inactive', guild_ids=[int(settings.DISCORD_GUILD_ID)])
    async def inactive_moons(self, ctx, own_corp: Optional[bool] = False):
        """
        Print inactive Moons!
        """
        if own_corp:
            if not self.sender_has_corp_moon_perm(ctx):
                return await ctx.respond(f"You do not have permission to use this command.", ephemeral=True)
            user = DiscordUser.objects.get(
                uid=ctx.author.id).user.profile.main_character
            corps = CorporationAudit.objects.filter(
                corporation__corporation_id=user.corporation_id)
            corp_names = [f"{c.corporation.corporation_name}" for c in corps]
            if corps.count() > 0:
                await ctx.respond(f"Printing Inactive Drills for {', '.join(corp_names)}", ephemeral=True)
                await ctx.author.send(f"Printing Inactive Drills for {', '.join(corp_names)}")
            else:
                await ctx.respond(f"Your corp is not setup in Audit, please contact an admin.", ephemeral=True)

        else:
            if not self.sender_has_moon_perm(ctx):
                return await ctx.respond(f"You do not have permission to use this command.", ephemeral=True)
            corps = CorporationAudit.objects.filter(
                corporation__corporation_id__in=app_settings.PUBLIC_MOON_CORPS)
            corp_names = [f"{c.corporation.corporation_name}" for c in corps]
            if corps.count() > 0:
                await ctx.respond(f"Printing Inactive Drills for {', '.join(corp_names)}")
            else:
                await ctx.respond(f"Public corp is not setup, please contact an admin.")

        tzactive = timezone.now()
        fracks = MoonFrack.objects.filter(
            arrival_time__gte=tzactive, corporation__in=corps).values_list('structure_id')
        structures = Structure.objects.filter(structureservice__name__in=[
            "Moon Drilling"], corporation__in=corps).exclude(structure_id__in=fracks)
        messages = [f"{s.name}" for s in structures]
        n = 10
        chunks = [list(messages[i * n:(i + 1) * n])
                  for i in range((len(messages) + n - 1) // n)]
        for chunk in chunks:
            message = "\n".join(chunk)
            if own_corp:
                await ctx.author.send(f"```{message}```")
            else:
                await ctx.send(f"```{message}```")


def setup(bot):
    bot.add_cog(MoonsCog(bot))
