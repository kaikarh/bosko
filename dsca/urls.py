from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('', views.DaybookViewSet)

urlpatterns = [
    path('api/c', views.GeneralCreateView.as_view()),
    path('access-api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

app_name = "dsca"
urlpatterns = [
    path('', views.index, name='index'),
    path('list-all/', views.ListAllView.as_view(), name='listall'),
]
