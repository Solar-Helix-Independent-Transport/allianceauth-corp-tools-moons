from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db import models
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from corptools.models import CorporationAudit, EveItemType, MapConstellation, MapRegion, MapSystem, MapSystemMoon, EveLocation, Notification, EveName
from django.db.models import Subquery, OuterRef
from django.db.models import FloatField, F, ExpressionWrapper

from . import app_settings
from django.utils import timezone

from invoices.models import Invoice
from .managers import MoonManager

if app_settings.discord_bot_active():
    import aadiscordbot

from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model

import logging
import copy
import json

logger = logging.getLogger(__name__)


class MoonFrack(models.Model):
    objects = MoonManager()

    corporation = models.ForeignKey(CorporationAudit, on_delete=models.CASCADE, related_name='moon')

    moon_name = models.ForeignKey(MapSystemMoon, on_delete=models.SET_NULL, null=True, default=None)
    moon_id = models.IntegerField()

    notification = models.ForeignKey(Notification, on_delete=models.SET_NULL, null=True, default=None)

    structure = models.ForeignKey(EveLocation, on_delete=models.CASCADE)

    start_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    auto_time = models.DateTimeField()

    #frack_pinged = models.BooleanField(default=False)
    #finish_notification = models.ForeignKey(Notification, on_delete=models.SET_NULL, null=True, default=None)
    #frack_notification = models.ForeignKey(Notification, on_delete=models.SET_NULL, null=True, default=None)
    
    class Meta:
        unique_together = (('arrival_time', 'moon_id'),)

    def __str__(self):
        return "{} - {}".format(self.moon_name.name, self.arrival_time)

    class Meta:
        permissions = (('view_available', 'Can View Configured Public Moons'),
                       ('view_corp', 'Can View Own Corps Moons'),  # these do nothing as of now.
                       ('view_alliance', 'Can View Own Alliances Moons'),
                       ('view_all', 'Can View All Moons'))


class FrackOre(models.Model):
    frack = models.ForeignKey(MoonFrack, on_delete=models.CASCADE, related_name='frack')
    ore = models.ForeignKey(EveItemType, on_delete=models.CASCADE)
    total_m3 = models.DecimalField(max_digits=20, decimal_places=2)


# Corp Mining Observation
class MiningObservation(models.Model):
    ob_pk = models.CharField(max_length=50, primary_key=True)

    observing_corporation = models.ForeignKey(CorporationAudit, on_delete=models.SET_NULL, null=True, default=None)

    observing_id = models.BigIntegerField(null=True, default=None, blank=True)
    structure = models.ForeignKey(EveLocation, on_delete=models.CASCADE, null=True, default=None, blank=True)
    moon = models.ForeignKey(MapSystemMoon, on_delete=models.SET_NULL, null=True, default=None, blank=True)

    character_name = models.ForeignKey(EveName, on_delete=models.SET_NULL, null=True, default=None)

    character_id = models.IntegerField()
    last_updated = models.DateTimeField()
    quantity = models.BigIntegerField()
    recorded_corporation_id = models.IntegerField()

    type_name = models.ForeignKey(EveItemType, on_delete=models.SET_NULL, null=True, default=None) 
    type_id = models.IntegerField()

    @classmethod
    def build_pk(cls, corp_id, observer_id, observed_character_id, ob_date, type_id):
        """
        Helper method to get a unique pk for a specific observation. Usefull for bulk updates of data.
        :param corp_id: Observer Corp.
        :param observer_id: Mining Observer ID.
        :param observed_character_id: Character Observed.
        :param ob_date: DateTime of observation.
        :return: :class:String
        """
        date_str = ob_date.strftime("%Y%m%d")
        return "{}-{}-{}-{}-{}".format(corp_id,
                                    observer_id,
                                    observed_character_id,
                                    date_str,
                                    type_id)

    class Meta:
        indexes = (
            models.Index(fields=['observing_id']),
            models.Index(fields=['last_updated']),
            models.Index(fields=['recorded_corporation_id']),
            models.Index(fields=['type_id']),
            models.Index(fields=['character_id'])
        )


    @classmethod
    def tax_moons(cls, start, end):
        #get all tax items and return the tax for the time period.

        player_data = {}
        observerd_ids = []
        observers_taxed = []

        taxes = MiningTax.objects.all().order_by('-rank')

        for tax in taxes:

            type_price = OrePrice.objects.filter(item_id=OuterRef('type_id'))

            observed = MiningObservation.objects.select_related('structure', 'type_name', 'structure__system', 'structure__system__constellation', 'character_name').all() \
                .annotate(isk_value=ExpressionWrapper(
                    Subquery(type_price.values('price')) * F('quantity'),
                        output_field=FloatField())) 
            
            if tax.use_variable_tax:
                tax_price = OreTax.objects.filter(item_id=OuterRef('type_id'), tax=tax.tax_rate)
                observed = observed.annotate(tax_value=ExpressionWrapper(
                    Subquery(tax_price.values('price')) * F('quantity'),
                        output_field=FloatField())) 
                
            observed = observed.filter(last_updated__gte=start).filter(last_updated__lt=end)

            if tax.corp:
                observed = observed.filter(observing_corporation__corporation=tax.corp)
            if tax.region:
                observed = observed.filter(structure__system__constellation__region=tax.region)
            if tax.constellation:
                observed = observed.filter(structure__system__constellation=tax.constellation)
            if tax.system:
                observed = observed.filter(structure__system=tax.system)
            if tax.moon:
                observed = observed.filter(moon=tax.moon)

            rate = float(tax.flat_tax_rate)
            # do the ranks
            observed = observed.exclude(structure__in=observers_taxed)
            #print(observed.query)
            #print(observed.count())

            for i in observed.distinct():
                if i.structure not in observers_taxed:
                    observers_taxed.append(i.structure)
                if i.ob_pk not in observerd_ids:
                    observerd_ids.append(i.ob_pk)
                    if i.character_name.eve_id not in player_data:
                        player_data[i.character_name.eve_id] = {}
                        player_data[i.character_name.eve_id]['ores'] = {}
                        player_data[i.character_name.eve_id]['totals_isk'] = 0
                        player_data[i.character_name.eve_id]['tax_isk'] = 0
                        player_data[i.character_name.eve_id]['character_model'] = i.character_name
                        player_data[i.character_name.eve_id]["seen_at"] = []
                    
                    if i.structure.location_name not in player_data[i.character_name.eve_id]["seen_at"]:
                        player_data[i.character_name.eve_id]["seen_at"].append(i.structure.location_name)

                    player_data[i.character_name.eve_id]['totals_isk'] =player_data[i.character_name.eve_id]['totals_isk'] + i.isk_value
                    
                    if tax.use_variable_tax:
                        player_data[i.character_name.eve_id]['tax_isk'] = player_data[i.character_name.eve_id]['tax_isk'] + i.tax_value
                    else:
                        player_data[i.character_name.eve_id]['tax_isk'] = player_data[i.character_name.eve_id]['tax_isk'] + i.isk_value * rate
                            

                    if i.type_name not in player_data[i.character_name.eve_id]['ores']: 
                        player_data[i.character_name.eve_id]['ores'][i.type_name.name] = {}
                        player_data[i.character_name.eve_id]['ores'][i.type_name.name]["type_id"] = i.type_id
                        player_data[i.character_name.eve_id]['ores'][i.type_name.name]["value"] = i.isk_value
                        player_data[i.character_name.eve_id]['ores'][i.type_name.name]["count"] = i.quantity
                    else:
                        player_data[i.character_name.eve_id]['ores'][i.type_name.name]["value"] = player_data[i.character_name.eve_id]['ores'][i.type_name.name]["value"]+i.isk_value
                        player_data[i.character_name.eve_id]['ores'][i.type_name.name]["count"] = player_data[i.character_name.eve_id]['ores'][i.type_name.name]["count"]+i.quantity


        output = {
            'player_data': player_data
        }

        return output


class OreTaxRates(models.Model):
    tag = models.CharField(max_length=500, default="Mining Tax")
    refine_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=87.5)
    ore_rate = models.DecimalField(max_digits=5, decimal_places=2)  # normal
    ubiquitous_rate = models.DecimalField(
        max_digits=5, decimal_places=2)  # ubiq
    common_rate = models.DecimalField(max_digits=5, decimal_places=2)  # comon
    uncommon_rate = models.DecimalField(
        max_digits=5, decimal_places=2)  # uncom
    rare_rate = models.DecimalField(max_digits=5, decimal_places=2)  # rare
    exceptional_rate = models.DecimalField(
        max_digits=5, decimal_places=2)  # best

    def __str__(self):
        try:
            return self.tag
        except:
            return "Mining Tax"


# Market History ( GMetrics )
class OrePrice(models.Model):
    item = models.ForeignKey(EveItemType, on_delete=models.DO_NOTHING, related_name='ore_price')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    last_update = models.DateTimeField(auto_now=True)


# tax rates History
class OreTax(models.Model):
    item = models.ForeignKey(EveItemType, on_delete=models.DO_NOTHING, related_name='ore_tax')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    last_update = models.DateTimeField(auto_now=True)
    tax = models.ForeignKey(OreTaxRates, on_delete=models.CASCADE, related_name='tax_rate')


class MiningTax(models.Model):
    corp = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name='moon_mining_tax', null=True, default=None, blank=True)
    tax_rate = models.ForeignKey(
        OreTaxRates, on_delete=models.CASCADE, null=True, default=None, blank=True)
    use_variable_tax = models.BooleanField(default=False)
    flat_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0)  # best
    region = models.ForeignKey(
        MapRegion, on_delete=models.CASCADE, related_name='tax_region', null=True, default=None, blank=True)
    constellation = models.ForeignKey(
        MapConstellation, on_delete=models.CASCADE, related_name='tax_constellation', null=True, default=None, blank=True)
    system = models.ForeignKey(
        MapSystem, on_delete=models.CASCADE, related_name='tax_system', null=True, default=None, blank=True)
    moon = models.ForeignKey(
        MapSystemMoon, on_delete=models.CASCADE, related_name='tax_moon', null=True, default=None, blank=True)
    rank = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        area = "Everywhere"
        if self.region:
            area = f"Region: {self.region.name}"
        elif self.constellation:
            area = f"Constellation: {self.constellation.name}"
        elif self.system:
            area = f"System: {self.system.name}"
        elif self.moon:
            area = f"Moon': {self.moon.name}"
        
        corp = "Everyone"
        if self.corp:
            corp = self.corp.corporation_name

        # return
        rate = ""
        if self.use_variable_tax:
            rate = " Variable ({})".format(self.tax_rate.tag)
        else:
            rate = "{}%".format(self.flat_tax_rate*100)
        return "#{3}: Mining Tax {0} for {1}, {2}".format(rate, corp, area, self.rank)


# tax rates History
class InvoiceRecord(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    ore_prices = models.TextField()
    tax_dump = models.TextField()
    total_mined = models.DecimalField(max_digits=20, decimal_places=2)
    total_taxed = models.DecimalField(max_digits=20, decimal_places=2)
    base_ref = models.CharField(max_length=72, default="")

    @classmethod
    def sanitize_date(cls, date):
        return datetime(year=date.year, 
                        month=date.month, 
                        day=date.day, 
                        tzinfo=date.tzinfo, 
                        hour=0,
                        minute=0,
                        second=0)


    @classmethod
    def get_last_invoice_date(cls):
        try:
            return InvoiceRecord.objects.all().order_by('-end_date').first().end_date
        except (ObjectDoesNotExist, AttributeError) as e:
            return datetime.min
    

    @classmethod
    def generate_invoice(cls, character, ref, amount, message):
        #generate an invoice and return it
        due = timezone.now() + timedelta(days=14)
        return Invoice(character=character,
                       amount=amount,
                       invoice_ref=ref,
                       note=message,
                       due_date=due)


    @classmethod
    def ping_invoice(cls, inv):
        # ping the invoice to the user ( if we know them )
        message = "\nPlease check auth for how to pay your mining Taxes!"
        inv.notify(message, title="Mining Taxes")


    @classmethod
    def generate_message(cls, raw_data):
        # Mining data for the invoice message, characters and stations
        pass


    @classmethod
    def generate_inv_ref(cls, char_id, start, end):
        date_str = "%Y%m%d"
        start_str = start.strftime(date_str)
        end_str = end.strftime(date_str)
        return f"MT{char_id}-{start_str}-{end_str}"


    @classmethod
    def generate_invoice_data(cls):
        start_date = cls.sanitize_date(cls.get_last_invoice_date())
        end_date = cls.sanitize_date(timezone.now())
        taxes = {}

        tax_data = MiningObservation.tax_moons(start_date, end_date)
        p_d = copy.deepcopy(tax_data['player_data'])

        all_ownerships = CharacterOwnership.objects.filter(character__character_id__in=tax_data['player_data'].keys()) 

        for o in all_ownerships:
            if o.user.id not in taxes:
                taxes[o.user.id] = {
                    "user": o.user,
                    "locations": set(),
                    "characters": set(),
                    "total_value": 0,
                    "tax_value": 0,
                    "ref": cls.generate_inv_ref(o.user.id, start_date, end_date)
                }

            tx = p_d.pop(o.character.character_id)

            taxes[o.user.id]['characters'].add(tx.get('character_model').name)
            taxes[o.user.id]['locations'].update(tx.get('seen_at'))
            taxes[o.user.id]['total_value'] += tx.get('totals_isk')
            taxes[o.user.id]['tax_value'] += tx.get('tax_isk')
            
            del tx

        return {"knowns": taxes, 
                "unknowns": p_d, 
                "start": start_date, 
                "end": end_date}


    @classmethod
    def generate_invoices(cls):
        from moons.helpers import OreHelper
        data = cls.generate_invoice_data()
        total_mined = 0
        total_taxed = 0
        # run known people
        for u, d in data['knowns'].items():
            try:
                ref = d['ref']
                amount = d['tax_value']

                total_mined += d['total_value']
                total_taxed += d['tax_value']

                character = d['user'].profile.main_character

                message = f"Mining Taxes for: {', '.join(d['characters'])}\nAt: {', '.join(d['locations'])}"
                inv = cls.generate_invoice(character, ref, amount, message)
                inv.save()
                cls.ping_invoice(inv)
            except KeyError:
                pass # probably wanna ping admin about it.
            except Exception:
                logger.exception(f"Failed to add invoice for {u}:\n\n{d}")

        for u, d in data['unknowns'].items():
            try:
                ref = cls.generate_inv_ref(d['character_model'].eve_id, data['start'], data['end'])
                amount = d['tax_isk']

                total_mined += d['totals_isk']
                total_taxed += d['tax_isk']

                try: 
                    character = EveCharacter.objects.get(character_id=d['character_model'].eve_id)
                except EveCharacter.DoesNotExist:
                    character = EveCharacter.objects.create_character(character_id=d['character_model'].eve_id)

                message = f"Mining Taxes for: {character.character_name} \nAt: {', '.join(d['seen_at'])}"
                inv = cls.generate_invoice(character, ref, amount, message)
                inv.save()
            except KeyError:
                pass # probably wanna ping admin about it.
            except Exception:
                logger.exception(f"Failed to add invoice for {u}:\n\n{d}")
                
        return cls.objects.create(start_date= data['start'],
                           end_date= data['end'],
                           tax_dump= json.dumps(data, cls=ExtendedJsonEncoder),
                           ore_prices= json.dumps(OreHelper.get_ore_array_with_value(), cls=ExtendedJsonEncoder),
                           total_mined=total_mined,
                           total_taxed=total_taxed,
                           base_ref=cls.generate_inv_ref("[id]",  data['start'],  data['end'])
                           )


class ExtendedJsonEncoder(DjangoJSONEncoder):

    def default(self, o):

        if isinstance(o, User):
            return {"user_id": o.pk}

        if isinstance(o, Model):
            return model_to_dict(o)

        if isinstance(o, set):
            return list(o)

        return super().default(o)
