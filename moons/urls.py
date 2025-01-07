from django.urls import path, re_path

from . import views
from .api import api

app_name = 'moons'

urlpatterns = [
    path('', views.extractions, name='list'),
    re_path(r'^data/', views.observers, name='data'),
    re_path(r'^r/', views.react, name='r'),
    re_path(r'^api/', api.urls),
    re_path(r'^report/usage', views.moon_report_use, name='report_use'),

]
