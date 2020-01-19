from django.urls import path

from . import views

urlpatterns = [
    path(r'logout/', views.logout_view, name='logout'),
    path(r'change_pwd/', views.change_pwd, name='change_pwd'),
]