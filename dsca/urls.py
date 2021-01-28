from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('', views.DaybookViewSet)

urlpatterns = [
    path('', views.index),
    path('api/c', views.GeneralCreateView.as_view()),
    path('access-api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
