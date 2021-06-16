from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r'daybook', views.DaybookViewSet)

app_name = "dsca"
urlpatterns = [
    path('', views.index, name='index'),
    path('list-all/', views.ListAllView.as_view(), name='listall'),
    path('api/c', views.GeneralCreateView.as_view()),
]
