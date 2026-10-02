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

### Moon values and rental suggestions

**Moons > Moon Values** ranks scanned moons by estimated value and tax per 30 days of extraction, priced under an Ore Tax Rates profile. In admin, tick **Show in moon values** on each profile you want to offer.

- Value: ore price at the profile's refine rate (honouring "ignore ores in refine" and "tax on base ore value").
- Tax: what the profile would tax that ore.

When creating a rental from **Moons > Rentals > New Rental**, the 30 day tax under a chosen profile is shown as a suggested monthly price. It is only a suggestion; the price you enter is what gets invoiced.

### Permissions

| Permission                | Allows                                                        |
| ------------------------- | ------------------------------------------------------------- |
| `moons.add_moonscan`      | Import scans for moons that have none                         |
| `moons.change_moonscan`   | Overwrite a moon's scan when a re-import differs              |
| `moons.view_moonscan`     | See scan compositions and the Moon Values ranking (all moons) |
| `moons.add_moonrental`    | Create rentals and see price suggestions                      |
| `moons.change_moonrental` | See price suggestions                                         |

### MOONS_DRILL_M3_PER_HOUR

`MOONS_DRILL_M3_PER_HOUR = 40000`

- The moon drill extraction rate used for values. 40,000 m3/h has applied to every Athanor and Tatara since December 2021; structure rigs don't change it.
