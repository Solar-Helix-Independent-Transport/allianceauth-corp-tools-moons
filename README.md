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
 0. this app is built on corptools and invoices. install them first.
 1. `pip install allianceauth-corptools-moons`
 2. set your "public" moons variable in `local.py`
 ```python
    PUBLIC_MOON_CORPS = [1234, 56789, 101112] # where the numbers are the corp ids
 ```
 3. run migrations
 4. run the setup management task 
 ```
    python manage.py setup_moon_tool
 ```
 5. wait for the tasks to finish.
 6. you need to ensure all your corps have pulled data and are working correctly before you invoice for the first time.
 7. setup your tax brackets and taxation rates / zones in admin
    
    admin > moons > mining tax ( Highest rank is run first )

    check the settings in console

 ```
    python manage.py current_tax_outstanding
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
 8. once you are happy, open admin and enable and then run the `Send Moon Invoices` task. This will now run every 14 days.
