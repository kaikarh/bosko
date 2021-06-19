from django.urls import path

from . import views

urlpatterns = [
    path('clicked', views.LinkClickedEntryCreateAPIView.as_view(), name='linkclickedentry-api-create'),
]
