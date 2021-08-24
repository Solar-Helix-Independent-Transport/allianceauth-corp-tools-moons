from django.conf.urls import url

from . import views
app_name = 'moons'

urlpatterns = [
    url(r'^$', views.extractions, name='list'),
    url(r'data/', views.observers, name='data'),
]