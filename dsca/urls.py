from django.urls import path, include

from . import views

app_name = "dsca"
urlpatterns = [
    path('', views.index, name='index'),
    path('daybook/', views.LinkClickedEntryListView.as_view(), name='linkclickedentry-list'),
]
