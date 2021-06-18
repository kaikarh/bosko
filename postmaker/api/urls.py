from django.urls import path, re_path, include
from rest_framework import routers
from rest_framework.authtoken import views as auth_views

from . import views

router = routers.SimpleRouter()
router.register(r'release', views.ReleaseAPIViewSet)

np_patterns = [
    path('login/', views.NpAccountLoginAPIView.as_view()),
    re_path(
        r'^post/(?P<action>(new)|(edit))/$',
        views.NpPostActionAPIView.as_view(),
        name='np-api-post-action'
    ),
    path('post-with-id/', views.NpPostReleaseWithaIDAPIView.as_view()),
    path('set-posted/', views.NpSetReleaseAsPostedAPIView.as_view()),
]

baal_patterns = [
    path('share/', views.BaalCreateShareLinkAPIView.as_view()),
]

urlpatterns = [
    path('np/', include(np_patterns)),
    path('baal/', include(baal_patterns)),
    path('am/', views.AplMusicFetchContentAPIView.as_view()),
    path('api-token/', auth_views.obtain_auth_token),
]