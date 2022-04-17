from allianceauth.services.hooks import MenuItemHook, UrlHook
from django.utils.translation import gettext_lazy as _
from allianceauth import hooks
from . import urls


class MoonsBetaHook(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(self,
                              _('Moon Board'),
                              'fas fa-moon fa-fw',
                              'moons:r',
                              navactive=['moons:r'])

    def render(self, request):
        if (request.user.has_perm('moons.view_available') or
            request.user.has_perm('moons.view_corp') or
            request.user.has_perm('moons.view_alliance') or
                request.user.has_perm('moons.view_all')):
            return MenuItemHook.render(self, request)
        return ''


@hooks.register('menu_item_hook')
def register_beta_menu():
    return MoonsBetaHook()


@hooks.register('url_hook')
def register_url():
    return UrlHook(urls, 'moons', r'^m/')


@hooks.register('discord_cogs_hook')
def register_cogs():
    return ["moons.mooncogs"]
