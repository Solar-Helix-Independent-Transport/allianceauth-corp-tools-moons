from django.conf.urls import url
from .api import api

from . import views
app_name = 'moons'

urlpatterns = [
    url(r'^$', views.extractions, name='list'),
    url(r'^data/', views.observers, name='data'),
    url(r'^r/', views.react, name='r'),
    url(r'^api/', api.urls),

]
