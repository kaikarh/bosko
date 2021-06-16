from django.urls import path

from django.views.generic.base import RedirectView

from . import views

app_name = 'postmaker'
urlpatterns = [
    path('', views.main),
    path('np', views.np, name='np'),
    path('release/', views.ReleaseList.as_view(), name='release_list'),
    path('release/<int:pk>/', views.ReleaseDetailView.as_view(), name='release_detail'),
    path('release/<int:pk>/edit', views.ReleaseEditView.as_view(), name='release-edit'),
    path('release/<int:pk>/edit/link', views.ReleaseLinkEditView.as_view(), name='release-link-edit'),
    path('release/<int:pk>/makepost/', views.ReleaseAlbumPostCreateView.as_view(), name='release-albumpost-create'),
    path('release-<type>/', views.ReleaseList.as_view(), name='release_list_type_filtered'),
    path('albumpost/make/', views.AlbumPostCreateView.as_view(), name='albumpost-create'),
    path('albumpost/result/', views.AlbumPostResultView.as_view(), name='albumpost-result'),
    path('albumpost/', RedirectView.as_view(pattern_name='postmaker:albumpost-create'), name='albumpost-redirect'),
    path('api/set-posted', views.set_posted, name='set_posted'),
    path('api/am', views.fetch_am, name='fetch_am'),
    path('api/post-with-id', views.post_to_forum_with_id, name='post_with_id'),
    path('api/np/login', views.np_login, name='np_login'),
    path('api/np/get-user', views.np_get_user, name='np_get_user'),
    path('api/np/post', views.np_post_thread, name='np_post_thread'),
    path('api/np/edit', views.np_edit_thread, name='np_edit_thread'),
    path('api/baal/share', views.get_share_link, name='get_share_link'),
    path('api/new-release', views.new_release_ping, name='new_release_ping'),
]