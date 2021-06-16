from django.urls import path, re_path, include
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r'release', views.ReleaseAPIViewSet)

np_patterns = [
    path('login/', views.NpAccountLoginAPIView.as_view()),
    re_path(
        r'^post/(?P<action>(new)|(edit))$',
        views.NpPostActionAPIView.as_view(),
        name='np-api-post-action'
    ),
]

urlpatterns = [
    path('np/', include(np_patterns)),
]