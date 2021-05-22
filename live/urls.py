from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('live/', views.live, name='live'),
    path('drop/', views.drop, name='drop'),
]