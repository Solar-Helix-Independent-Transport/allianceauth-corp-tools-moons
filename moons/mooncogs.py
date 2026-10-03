# Cog Stuff
import asyncio
import logging
# AA Contexts
from decimal import Decimal
from typing import Optional

from aadiscordbot.app_settings import get_all_servers
from aadiscordbot.cogs.utils.decorators import has_any_perm
from aadiscordbot.utils.auth import get_auth_user
from corptools.models import CorporationAudit, Structure
from discord import AutocompleteContext, option
from discord.commands import SlashCommandGroup
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands import Paginator
from eve_sde.models import Moon

from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

from moons import app_settings, rent, scans
from moons.models import (
    InvoiceRecord, MoonFrack, MoonRental, MoonScan, OreTaxRates,
)

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
        "moons", "Moon Module Commands", guild_ids=get_all_servers())

    def sender_has_moon_perm(self, ctx):
        has_perm = has_any_perm(ctx.author.id, ["moons.view_all"], guild=ctx.guild)
        if has_perm:
            return True
        else:
            return False

    def sender_has_corp_moon_perm(self, ctx):
        has_perm = has_any_perm(ctx.author.id, ["moons.view_corp"], guild=ctx.guild)
        if has_perm:
            return True
        else:
            return False

    async def search_corp_names(ctx: AutocompleteContext):
        return list(EveCorporationInfo.objects.filter(
            corporation_name__icontains=ctx.value).values_list("corporation_name", flat=True)[:10])

    def sender_has_moon_rental_create_perm(self, ctx):
        has_perm = has_any_perm(ctx.author.id, ["moons.change_moonrental"], guild=ctx.guild)
        if has_perm:
            return True
        else:
            return False

    @pinger_commands.command(name='print_stats', guild_ids=get_all_servers())
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

    @pinger_commands.command(name='inactive', guild_ids=get_all_servers())
    async def inactive_moons(self, ctx, own_corp: Optional[bool] = False):
        """
        Print inactive Moons!
        """
        if own_corp:
            if not self.sender_has_corp_moon_perm(ctx):
                return await ctx.respond(f"You do not have permission to use this command.", ephemeral=True)
            user = get_auth_user(ctx.user, ctx.guild).profile.main_character
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

    # Moon pricing from imported scans; same valuation as the Moon Values page

    def sender_can_price_moons(self, ctx):
        return any(
            has_any_perm(ctx.author.id, [perm], guild=ctx.guild)
            for perm in ("moons.view_moonscan", "moons.add_moonrental", "moons.change_moonrental")
        )

    async def search_scanned_moons(ctx: AutocompleteContext):
        return list(MoonScan.objects.filter(
            moon__name__icontains=ctx.value).values_list("moon__name", flat=True)[:10])

    async def search_ore_taxes(ctx: AutocompleteContext):
        return list(OreTaxRates.objects.filter(
            tag__icontains=ctx.value).values_list("tag", flat=True)[:25])

    async def search_scanned_regions(ctx: AutocompleteContext):
        return list(MoonScan.objects.filter(
            moon__solar_system__constellation__region__name__icontains=ctx.value
        ).values_list("moon__solar_system__constellation__region__name", flat=True)
            .distinct()[:10])

    @staticmethod
    def _ore_tax(tag):
        # any ore tax can be picked; the default is the first one offered on Moon Values
        if tag:
            return OreTaxRates.objects.filter(tag=tag).first()
        return OreTaxRates.objects.filter(show_in_moon_values=True).order_by("id").first()

    @staticmethod
    async def _fuel_for(tax_rate):
        if not tax_rate.rent_subtract_metenox_fuel:
            return None
        gas, blocks = await asyncio.to_thread(rent.fetch_fuel_prices)
        return rent.metenox_fuel_30d(gas, blocks)

    @pinger_commands.command(name='price', guild_ids=get_all_servers())
    @option("moon", description="A scanned moon", autocomplete=search_scanned_moons)
    @option("ore_tax", description="Ore tax to price with (default: first shown on Moon Values)", autocomplete=search_ore_taxes, required=False)
    @option("explain", description="Show every input step by step", required=False)
    async def price_moon(self, ctx, moon: str, ore_tax: str = None, explain: bool = False):
        """
        Value a scanned moon and suggest its rent.
        """
        if not self.sender_can_price_moons(ctx):
            return await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        await ctx.defer()

        tax_rate = self._ore_tax(ore_tax)
        if not tax_rate:
            if ore_tax:
                return await ctx.respond(f"No ore tax called `{ore_tax}`.")
            return await ctx.respond("Pick an ore tax, or tick 'show in moon values' on one to make it the default.")
        moon_id = Moon.objects.filter(name=moon).values_list("id", flat=True).first()
        values = scans.moon_values(tax_rate, moon_ids=[moon_id]) if moon_id else []
        if not values:
            return await ctx.respond(f"No scan for `{moon}`.")
        v = values[0]
        fuel = await self._fuel_for(tax_rate)
        r = rent.rent_breakdown(v.tax_30d, tax_rate, fuel)
        m3_per_hour = tax_rate.drill_m3_per_hour or app_settings.drill_m3_per_hour()

        msg = Paginator()
        msg.add_line(f"{v.name}  ({v.system} / {v.region})  R{v.rarity or '-'}")
        msg.add_line(f"Ore tax `{tax_rate.tag}`, 30 days at {m3_per_hour:,} m3/h")
        msg.add_line("-" * 60)
        for line in v.ore_lines:
            msg.add_line(f"{line.name.ljust(24)}{line.fraction * 100:6.2f}%")
            if explain:
                value = f"Ƶ{line.unit_value:,.2f}" if line.unit_value is not None else "unpriced"
                msg.add_line(f"    {line.units:,.0f} units, value {value}/unit, tax Ƶ{line.unit_tax:,.2f}/unit"
                             f" = Ƶ{line.units * line.unit_tax:,.0f}")
        if v.total_fraction < Decimal("0.995"):
            msg.add_line(f"(composition totals {v.total_fraction * 100:.1f}%, not scaled up)")
        msg.add_line("-" * 60)
        msg.add_line(f"Value 30d:          Ƶ{v.value_30d:,.0f}")
        msg.add_line(f"Tax 30d:            Ƶ{r.tax_30d:,.0f}")
        if r.fuel:
            f = r.fuel
            if explain:
                msg.add_line(f"  Gas Ƶ{f.gas_price:,.2f} (adjusted Ƶ{f.gas_adjusted:,.2f}) x 720 h x {f.gas_per_hour}/h"
                             f" = Ƶ{f.gas_30d:,.0f}")
                msg.add_line(f"  Blocks avg Ƶ{f.block_average:,.2f} x 720 h x {rent.BLOCKS_PER_HOUR}/h"
                             f" = Ƶ{f.blocks_30d:,.0f}")
            msg.add_line(f"Metenox fuel 30d:   Ƶ{f.total_30d:,.0f}")
            msg.add_line(f"Profit:             Ƶ{r.profit:,.0f}")
        if r.share != 100:
            msg.add_line(f"Share {r.share}%:        Ƶ{r.raw:,.0f}")
        msg.add_line(f"Rounded to 1m:      Ƶ{r.rounded:,.0f}")
        if r.final != r.rounded:
            msg.add_line(f"Minimum applied:    Ƶ{r.final:,.0f}")
        msg.add_line(f"Suggested rent:     Ƶ{r.final:,.0f}")
        rental = MoonRental.objects.filter(moon_id=moon_id, end_date__isnull=True).select_related("contact").first()
        if rental:
            msg.add_line(f"Current rent:       Ƶ{rental.price:,.0f} ({rental.contact.character_name}),"
                         f" delta Ƶ{r.final - rental.price:,.0f}")

        await ctx.respond(f"Pricing `{v.name}`")
        for page in msg.pages:
            await ctx.send(page)

    @pinger_commands.command(name='rental_recalc', guild_ids=get_all_servers())
    @option("region", description="Region of the rented moons", autocomplete=search_scanned_regions)
    @option("ore_tax", description="Ore tax to price with (default: first shown on Moon Values)", autocomplete=search_ore_taxes, required=False)
    @option("exclude_corp", description="Skip rentals by this corporation", autocomplete=search_corp_names, required=False)
    async def rental_recalc(self, ctx, region: str, ore_tax: str = None, exclude_corp: str = None):
        """
        Compare every active rental in a region with its suggested rent. Changes nothing.
        """
        if not self.sender_has_moon_rental_create_perm(ctx):
            return await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        await ctx.defer()

        tax_rate = self._ore_tax(ore_tax)
        if not tax_rate:
            if ore_tax:
                return await ctx.respond(f"No ore tax called `{ore_tax}`.")
            return await ctx.respond("Pick an ore tax, or tick 'show in moon values' on one to make it the default.")
        rentals = MoonRental.objects.filter(
            moon__solar_system__constellation__region__name=region,
            end_date__isnull=True, price__gte=1,
        ).select_related("moon", "contact")
        if exclude_corp:
            rentals = rentals.exclude(corporation__corporation_name=exclude_corp)
        rentals = list(rentals)
        values = {v.moon_id: v for v in scans.moon_values(tax_rate, moon_ids=[r.moon_id for r in rentals])}
        fuel = await self._fuel_for(tax_rate)

        msg = Paginator()
        msg.add_line(f"Rental recalculation: {region}, ore tax `{tax_rate.tag}`")
        if fuel:
            msg.add_line(f"Metenox fuel 30d Ƶ{fuel.total_30d:,.0f} (gas Ƶ{fuel.gas_adjusted:,.0f}, blocks Ƶ{fuel.block_average:,.0f})")
        msg.add_line(f"{'Moon'.ljust(30)}{'Current'.rjust(16)}{'Suggested'.rjust(16)}{'Delta'.rjust(16)}")
        total_old = total_new = 0
        no_scan = []
        for rental in sorted(rentals, key=lambda r: r.moon.name):
            v = values.get(rental.moon_id)
            if not v:
                no_scan.append(f"{rental.moon.name} ({rental.contact.character_name})")
                continue
            new = rent.rent_breakdown(v.tax_30d, tax_rate, fuel).final
            total_old += rental.price
            total_new += new
            msg.add_line(f"{rental.moon.name[:29].ljust(30)}{f'{rental.price:,}'.rjust(16)}"
                         f"{f'{new:,}'.rjust(16)}{f'{new - rental.price:,}'.rjust(16)}")
        msg.add_line("-" * 78)
        msg.add_line(f"{'Total'.ljust(30)}{f'{total_old:,}'.rjust(16)}{f'{total_new:,}'.rjust(16)}"
                     f"{f'{total_new - total_old:,}'.rjust(16)}")
        if no_scan:
            msg.add_line(f"No scan ({len(no_scan)}):")
            for name in no_scan:
                msg.add_line(f"  - {name}")

        await ctx.respond(f"Recalculated {len(rentals)} rentals in {region}. Nothing was changed.")
        for page in msg.pages:
            await ctx.send(page)

    if app_settings.MOONS_ENABLE_RENT_COG:
        rental_commands = SlashCommandGroup(
            "moon_rentals", "Moon Rental Commands", guild_ids=get_all_servers())

        async def search_moons(ctx: AutocompleteContext):
            """Returns a list of moons that begin with the characters entered so far."""
            resp = list(Moon.objects.filter(
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

        @rental_commands.command(name='status', guild_ids=get_all_servers())
        @option("moon", description="Search for a Moon!", autocomplete=search_moons)
        async def moon_rental_status(self, ctx, moon: str):
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

        @rental_commands.command(name='character_status', guild_ids=get_all_servers())
        @option("character", description="Search for a Character!", autocomplete=search_characters)
        async def moon_rental_character_status(self, ctx, character: str):
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

        @rental_commands.command(name='rent', guild_ids=get_all_servers())
        @option("moon", description="Search for a Moon!", autocomplete=search_moons)
        @option("character", description="Search for a Character!", autocomplete=search_characters)
        @option("corporation", description="Search for a Corporation!", autocomplete=search_corp)
        @option("price", description="Price per month!")
        async def moon_rental_rent(self, ctx, moon: str, character: str, corporation: str, price: int = 100000000):
            """
            Rent a moon!
            """
            ctx.defer()
            if not self.sender_has_moon_rental_create_perm(ctx):
                return await ctx.respond(f"You do not have permission to use this command.", ephemeral=True)

            moon_q = MoonRental.objects.filter(
                moon__name=moon, end_date__isnull=True)

            if not moon_q.exists():
                moon = Moon.objects.get(name=moon)
                char = EveCharacter.objects.get(character_name=character)
                corp = EveCorporationInfo.objects.get(
                    corporation_name=corporation)
                MoonRental.objects.create(moon=moon, contact=char, corporation=corp,
                                          price=price, start_date=timezone.now(), note=f"rented by {ctx.author}")
                return await ctx.respond(f"Rented `{moon}` to `{character} [{corporation}]` for ${price:,}")
            else:
                return await ctx.respond(f"**Unable to rent** `{moon}` to `{character}` Already rented!")

        @rental_commands.command(name='unrent', guild_ids=get_all_servers())
        @option("moon", description="Search for a Moon!", autocomplete=search_moons)
        @option("character", description="Search for a Character!", autocomplete=search_characters)
        async def moon_rental_unrent(self, ctx, moon: str, character: str):
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
