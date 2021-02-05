from django.urls import path

from . import views

app_name = 'postmaker'
urlpatterns = [
    path('', views.main),
    path('make', views.make),
    path('api/get', views.fetchapi),
]
