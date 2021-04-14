from django.urls import path

from . import views

app_name = 'minos'
urlpatterns = [
    path('api/new', views.api_accept_release),
    path('rt', views.render_thread),
]
