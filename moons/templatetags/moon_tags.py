from django.template.defaulttags import register
from django.utils.safestring import mark_safe


@register.filter()
def ore_color(ore):
    try:
        if 'Bitumens' in ore or 'Coesite' in ore or 'Sylvite' in ore or 'Zeolite' in ore:
            return mark_safe('style="background-color:#9B1C31"')
        elif 'Cobalite' in ore or 'Euxenite' in ore or 'Scheelite' in ore or 'Titanite' in ore:
            return mark_safe('style="background-color:#FFAA1D"')
        elif 'Chromite' in ore or 'Otavite' in ore or 'Sperrylite' in ore or 'Vanadinite' in ore:
            return mark_safe('style="background-color:#E86100"')
        elif 'Carnotite' in ore or 'Cinnabar' in ore or 'Pollucite' in ore or 'Zircon' in ore:
            return mark_safe('style="background-color:#4B8B3B"')
        elif 'Loparite' in ore or 'Monazite' in ore or 'Xenotime' in ore or 'Ytterbite' in ore:
            return mark_safe('style="background-color:#0D98BA"')
        else:
            return mark_safe('style="background-color:#B57EDC"')

    except:
        #logging.exception("Messsage")
        return ""

