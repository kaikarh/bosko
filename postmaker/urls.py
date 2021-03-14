from django.urls import path

from . import views

app_name = 'postmaker'
urlpatterns = [
    path('', views.main),
    path('make', views.make, name='make'),
    path('np', views.np, name='np'),
    path('api/am', views.fetch_am, name='fetch_am'),
    path('api/np/login', views.np_login, name='np_login'),
    path('api/np/get-user', views.np_get_user, name='np_get_user'),
    path('api/np/post', views.np_post_thread, name='np_post_thread'),
    path('api/baal/share', views.get_share_link, name='get_share_link'),
]
