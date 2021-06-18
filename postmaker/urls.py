from django.urls import path

from django.views.generic.base import RedirectView

from . import views

app_name = 'postmaker'
urlpatterns = [
    path('', RedirectView.as_view(pattern_name='postmaker:albumpost-create')),
    path('release/', views.ReleaseList.as_view(), name='release-list'),
    path('release/<int:pk>/', views.ReleaseDetailView.as_view(), name='release-detail'),
    path('release/<int:pk>/edit', views.ReleaseEditView.as_view(), name='release-edit'),
    path('release/<int:pk>/edit/link', views.ReleaseLinkEditView.as_view(), name='release-link-edit'),
    path('release/<int:pk>/makepost/', views.ReleaseAlbumPostCreateView.as_view(), name='release-albumpost-create'),
    path('release-<type>/', views.ReleaseList.as_view(), name='release-list-type-filtered'),
    path('albumpost/make/', views.AlbumPostCreateView.as_view(), name='albumpost-create'),
    path('albumpost/result/', views.AlbumPostResultView.as_view(), name='albumpost-result'),
    path('albumpost/', RedirectView.as_view(pattern_name='postmaker:albumpost-create'), name='albumpost-redirect'),
]