"""bosko URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from rest_framework.routers import SimpleRouter

from dsca.urls import router as dsca_router
from postmaker.api.urls import router as postmaker_router

router = SimpleRouter()
router.registry.extend(dsca_router.registry)
router.registry.extend(postmaker_router.registry)

api_urls = [
    path('', include(router.urls)),
    path('', include('postmaker.api.urls')),
]

urlpatterns = [
    path('', include('generic.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dsca/', include('dsca.urls')),
    path('minos/', include('minos.urls')),
    path('postmaker/', include('postmaker.urls')),
    #path('admin/', admin.site.urls),
    path('api/', include((api_urls, 'v1'))),
]
