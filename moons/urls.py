from django.urls import re_path
from .api import api

from . import views
app_name = 'moons'

urlpatterns = [
    re_path(r'^$', views.extractions, name='list'),
    re_path(r'^data/', views.observers, name='data'),
    re_path(r'^r/', views.react, name='r'),
    re_path(r'^api/', api.urls),

]
