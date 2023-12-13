# Cog Stuff
from typing import Optional
from corptools.models import CorporationAudit, Structure
from discord import AutocompleteContext, Interaction, option
from discord.embeds import Embed
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.modules.discord.models import DiscordUser
from discord.ext import commands
from discord.commands import SlashCommandGroup

# AA Contexts
import pprint
from django.conf import settings
from django.utils import timezone
from moons.models import InvoiceRecord, MoonFrack, MoonRental
from corptools.models import MapSystemMoon

from moons import app_settings

import logging

logger = logging.getLogger(__name__)

BLUE = 0x3498db
MAGENTA = 0xe91e63
GREYPLE = 0x99aab5
RED = 0x992d22


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

    def sender_has_moon_rental_create_perm(self, ctx):
        id = ctx.author.id
        try:
            has_perm = DiscordUser.objects.get(
                uid=id).user.has_perm("moons.change_moonrental")
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

    if app_settings.MOONS_ENABLE_RENT_COG:
        rental_commands = SlashCommandGroup(
            "moon_rentals", "Moon Rental Commands", guild_ids=[int(settings.DISCORD_GUILD_ID)])

        async def search_moons(ctx: AutocompleteContext):
            """Returns a list of moons that begin with the characters entered so far."""
            resp = list(MapSystemMoon.objects.filter(
                name__icontains=ctx.value).values_list("name", flat=True)[:10])
            return resp

        async def search_characters(ctx: AutocompleteContext):
            """Returns a list of colors that begin with the characters entered so far."""
            resp = list(EveCharacter.objects.filter(
                character_name__icontains=ctx.value).values_list('character_name', flat=True)[:10])
            return resp

        async def search_corp(ctx: AutocompleteContext):
            """Returns a list of colors that begin with the characters entered so far."""
            resp = list(EveCorporationInfo.objects.filter(
                corporation_name__icontains=ctx.value).values_list('corporation_name', flat=True)[:10])
            return resp

        @rental_commands.command(name='status', guild_ids=[int(settings.DISCORD_GUILD_ID)])
        @option("moon", description="Search for a Moon!", autocomplete=search_moons)
        async def moon_rental_status(self, ctx: Interaction, moon: str):
            """
            Print Moons Status!
            """
            ctx.defer()
            if not self.sender_has_moon_rental_create_perm(ctx):
                return await ctx.respond(f"You do not have permission to use this command.", ephemeral=True)

            moon_q = MoonRental.objects.filter(
                moon__name=moon, end_date__isnull=True)

            msgs = []
            for m in MoonRental.objects.filter(moon__name=moon):
                msgs.append(
                    f"{m.start_date.strftime('%y-%m-%d')} to {m.end_date.strftime('%y-%m-%d') if m.end_date else ' ACTIVE '} by {m.contact} [{m.corporation}] for ${m.price:,}")
            msgs = "\n".join(msgs)

            if not moon_q.exists():
                return await ctx.respond(f"{moon} Available!\n```\n{msgs}\n```")
            else:
                return await ctx.respond(f"{moon} is rented!\n```\n{msgs}\n```")

        @rental_commands.command(name='character_status', guild_ids=[int(settings.DISCORD_GUILD_ID)])
        @option("character", description="Search for a Character!", autocomplete=search_characters)
        async def moon_rental_character_status(self, ctx: Interaction, character: str):
            """
            Print Moons Status!
            """
            ctx.defer()
            if not self.sender_has_moon_rental_create_perm(ctx):
                return await ctx.respond(f"You do not have permission to use this command.", ephemeral=True)

            moon_q = MoonRental.objects.filter(
                contact__character_name=character, end_date__isnull=True)

            msgs = []
            for m in moon_q:
                msgs.append(
                    f"{m.moon} by {m.contact} [{m.corporation}] for ${m.price:,}")
            msgs = "\n".join(msgs)

            if not moon_q.exists():
                return await ctx.respond(f"{character} has no rentals.")
            else:
                return await ctx.respond(f"{character} has rented!\n```\n{msgs}\n```")

        @rental_commands.command(name='rent', guild_ids=[int(settings.DISCORD_GUILD_ID)])
        @option("moon", description="Search for a Moon!", autocomplete=search_moons)
        @option("character", description="Search for a Character!", autocomplete=search_characters)
        @option("corporation", description="Search for a Corporation!", autocomplete=search_corp)
        @option("price", description="Price per month!")
        async def moon_rental_rent(self, ctx: Interaction, moon: str, character: str, corporation: str, price: int = 100000000):
            """
            Rent a moon!
            """
            ctx.defer()
            if not self.sender_has_moon_rental_create_perm(ctx):
                return await ctx.respond(f"You do not have permission to use this command.", ephemeral=True)

            moon_q = MoonRental.objects.filter(
                moon__name=moon, end_date__isnull=True)

            if not moon_q.exists():
                moon = MapSystemMoon.objects.get(name=moon)
                char = EveCharacter.objects.get(character_name=character)
                corp = EveCorporationInfo.objects.get(
                    corporation_name=corporation)
                MoonRental.objects.create(moon=moon, contact=char, corporation=corp,
                                          price=price, start_date=timezone.now(), note=f"rented by {ctx.author}")
                return await ctx.respond(f"Rented `{moon}` to `{character} [{corporation}]` for ${price:,}")
            else:
                return await ctx.respond(f"**Unable to rent** `{moon}` to `{character}` Already rented!")

        @rental_commands.command(name='unrent', guild_ids=[int(settings.DISCORD_GUILD_ID)])
        @option("moon", description="Search for a Moon!", autocomplete=search_moons)
        @option("character", description="Search for a Character!", autocomplete=search_characters)
        async def moon_rental_unrent(self, ctx: Interaction, moon: str, character: str):
            """
            Rent a moon!
            """
            ctx.defer()
            if not self.sender_has_moon_rental_create_perm(ctx):
                return await ctx.respond(f"You do not have permission to use this command.", ephemeral=True)

            moon_q = MoonRental.objects.filter(
                moon__name=moon, end_date__isnull=True)

            if moon_q.exists():
                m = moon_q.first()
                m.end_date = timezone.now()
                m.note += f"\nUnrented by {character}, completed by {ctx.author}"
                m.save()
                return await ctx.respond(f"Unrented `{moon}` from `{m.contact}` by `{character}`")
            else:
                return await ctx.respond(f"**Unable to unrent** `{moon}` no rental found?")


def setup(bot):
    bot.add_cog(MoonsCog(bot))
