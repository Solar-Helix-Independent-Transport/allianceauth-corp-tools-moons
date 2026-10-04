# Moon Tools

moon frack monitoring and taxation, taxation is calculated ( default, but configurable ) 2 weekly and includes all valid "taxes" from the period.

## tax options

- Corp Filter
- Rank system for all strucutres that are captured in a "Tax Group"
- Flat rate or configurable variable tax rates per ore type
  **More specific overrides the rest**
- Region filter
- Constellation Filter
- System Filter
- Moon Filter
- Jackpot ore taxed like plain ore (see below)

### Jackpot moon ore

Jackpot ore (Glistening, Shining and so on) refines into twice the minerals of its base ore, so it is worth, and taxed at, twice as much. To tax it like the plain ore instead:

- Variable rates: tick **Tax on base ore value** on the Ore Tax Rates profile.
- Flat rates: tick **Flat tax on base ore value** on the Mining Tax.

Either way, every variant of an ore is taxed at its base ore's value, while the mined value shown on invoices stays the real one.

## installation

0.  this app is built on corptools and invoices. install them first.
1.  `pip install allianceauth-corptools-moons`
2.  add 'moons' to your installed apps in local.py
3.  set your "public" moons variable in `local.py`

```python
   PUBLIC_MOON_CORPS = [1234, 56789, 101112] # where the numbers are the corp ids
```

3.  run migrations
4.  run the setup management task

```
   python manage.py moons_setup_tool
```

5.  wait for the tasks to finish.
6.  you need to ensure all your corps have pulled data and are working correctly before you invoice for the first time.
7.  setup your tax brackets and taxation rates / zones in admin

    admin > moons > mining tax ( Highest rank is run first )

    check the settings in console

```
   python manage.py moons_tax_outstanding
```

```
Calculating!
Last Invoice 2021-09-06 00:00:00+00:00!
Doing some math... Please wait...

We've seen 56 known members!
We've seen 12 unknown characters!

Who have mined $833,068,517,622.8707 worth of ore!
Current Tax puts this at $195,791,603,220.688 in taxes!

the structures included are:
[system] - [name]
[system] - [name]
[system] - [name]
[system] - [name]
[system] - [name]
[system] - [name]
```

8.  once you are happy, open admin and enable and then run the `Send Moon Invoices` task. This will now run every 14 days. You can freely edit the period of this task to match what your group requires.

## Ore Price Sources

### MOONS_ORE_RATE_BUY_SELL

`MOONS_ORE_RATE_BUY_SELL="buy"`

- Sets the ore prices to buy and uses the bucket defined in the `MOONS_ORE_RATE_BUCKET` option

`MOONS_ORE_RATE_BUY_SELL="sell"`

- Sets the ore prices to buy and uses the bucket defined in the `MOONS_ORE_RATE_BUCKET` option

`MOONS_ORE_RATE_BUY_SELL="split"`

- Sets the ore prices to a calculated split value and ignores bucket defined in the `MOONS_ORE_RATE_BUCKET` option
- `(Max Buy + Min Sell) / 2`

### MOONS_ORE_RATE_BUCKET

Sets the bucket used in buy/sell ore calculations:

- `MOONS_ORE_RATE_BUCKET="weightedAverage"`
- `MOONS_ORE_RATE_BUCKET="max"`
- `MOONS_ORE_RATE_BUCKET="min"`
- `MOONS_ORE_RATE_BUCKET="stddev"`
- `MOONS_ORE_RATE_BUCKET="median"`
- `MOONS_ORE_RATE_BUCKET="percentile"`

## Moon Scans

Import probe-scanner moon scans to rank moons by value and get rental price suggestions.

### Importing

In game, scan the moons with the probe scanner, select the results and copy them (Ctrl+C). Paste them into **Moons > Import Scans**, review, and confirm. Any client language works, and pastes relayed through Discord (tabs turned into spaces) are fine.

- Moons with no scan yet are imported.
- A re-import that matches the stored scan (to 4 decimal places) changes nothing; the original submitter keeps the credit.
- A re-import that differs replaces the stored scan, but only for users with the change permission.
- Unknown moons or ore types are rejected; ores that are no longer moon ores are kept and flagged.

Compositions are stored exactly as scanned. Moons under 100% are normal and are never scaled up.

Below the import, **Scan coverage** shows how many of a region's moons are scanned and lists the missing ones by system, so you know where to send scanners.

### Moon values and rental suggestions

**Moons > Moon Values** ranks the scanned moons of one region at a time by estimated value and tax per 30 days of extraction, priced under an Ore Tax Rates profile. In admin, tick **Show in moon values** on each profile you want to offer.

- Value: ore price at the profile's refine rate (honouring "ignore ores in refine" and "tax on base ore value").
- Tax: what the profile would tax that ore.
- Rent: the suggested monthly rent under the profile's rent options (below).
- Rental: whether the moon is rented (who rents it and for how much with `moons.view_moonrental`). Available moons have a **Rent** button for `moons.add_moonrental` that opens New Rental with the moon and the suggested rent filled in.

When creating a rental from **Moons > Rentals > New Rental**, the same suggested rent under a chosen profile is shown. It is only a suggestion; the price you enter is what gets invoiced.

### Discord commands

- `/moons price <moon> [ore_tax] [explain]` values a scanned moon under one of the ore taxes shown on Moon Values (default: the first) and suggests its rent. `explain` shows every input per ore.
- `/moons explain <moon> [ore_tax]` (same ore tax choices) works through the price step by step: the profile's inputs, then for each ore its units, OrePrice, value and tax (flagging stored ore taxes that no longer match prices), then Metenox fuel and the rent.
- `/moons rental_recalc <region> [ore_tax] [exclude_corp]` (same ore tax choices) lists every active rental in a region with its current and suggested rent. It changes nothing.

Moon Values, New Rental and these commands all suggest rent the same way: the 30 day tax, rounded to the nearest million, adjusted by these options on each tax profile:

- **Rent subtract Metenox fuel**: subtract 30 days of Metenox fuel (magmatic gas and fuel blocks, Jita prices from Fuzzwork, cached for an hour) from the tax.
- **Rent profit share**: the percent of what is left that is charged as rent.
- **Rent minimum**: the lowest rent ever suggested.

#### Repricing rentals

Each rental has a **reprice method**: the ore tax profile whose suggested rent it should be charged, or empty to leave its price alone. Set it when creating a rental, in the Rentals table's **Reprice** column (`moons.change_moonrental`), or in admin.

The `moons.tasks.reprice_rentals` task sets every active rental (price at least 1 ISK) that has a reprice method to that profile's suggested rent. Schedule it as a periodic task, e.g. monthly before invoicing. Its run settings are in admin under **Rental repricing settings** (created with the defaults on the first run):

- **Dry run**: only post the projected prices.
- **Notify renters** and **Channel ID**: DM each renter their new prices and post a run summary (needs the Discord bot).

Each changed rental gets `YYYY/MM/DD - Old: x - New: y` added to its notes. Rentals whose contact isn't owned by an auth user, or whose moon has no scan, are listed in the summary and left alone.

Fuel pricing settings: `MOONS_FUEL_BUY_SELL` (`"buy"`), `MOONS_FUEL_BUCKET` (`"percentile"`), `MOONS_FUEL_GAS_FACTOR` (`2`, softens gas above 10,000 ISK) and `MOONS_METENOX_GAS_PER_HOUR` (`200`).

### Permissions

| Permission                | Allows                                                        |
| ------------------------- | ------------------------------------------------------------- |
| `moons.add_moonscan`      | Import scans for moons that have none                         |
| `moons.change_moonscan`   | Overwrite a moon's scan when a re-import differs              |
| `moons.view_moonscan`     | See scan compositions and the Moon Values ranking (all moons) |
| `moons.add_moonrental`    | Create rentals and see price suggestions                      |
| `moons.change_moonrental` | See price suggestions, unrent moons (a note is required)      |

### MOONS_DRILL_M3_PER_HOUR

`MOONS_DRILL_M3_PER_HOUR = 40000`

- The moon drill extraction rate used for values. 40,000 m3/h has applied to every Athanor and Tatara since December 2021; structure rigs don't change it.
- A tax profile can set its own **Drill m3 per hour**, which wins over this setting. For Metenox moon drills, make a profile with drill m3 per hour `30000`, refine rate `40` and **ignore ores in refine** ticked (a Metenox outputs moon materials only, at 40% efficiency).
