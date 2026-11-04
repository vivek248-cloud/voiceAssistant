from django.urls import path
from .views import home, voice_api

urlpatterns = [
    path('', home, name='home'),
    path('voice/', voice_api, name='voice_api'),
]
