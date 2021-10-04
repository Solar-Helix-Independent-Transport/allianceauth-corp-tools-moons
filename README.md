# Moon Tools

moon frack monitoring and taxation, taxation is calculated ( default, but configurable ) 2 weekly and includes all valid "taxes" from the period.

## tax options 
 - Corp Filter
 - Rank system for all struccutres that are captured in a "Tax Group"
 - Flat rate or configurable variable tax rates per ore type
 **More specific overrides the rest**
 - Region filter
 - Constellation Filter
 - System Filter
 - Moon Filter

## installation
 0. this app is built on corptools and invoices. install them first.
 1. pip install allianceauth-corp-tools-moons
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
 8. once you are happy, open admin and enable and then run the `Send Moon Invoices` task.
