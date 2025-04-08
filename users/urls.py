from django.urls import path
from . import views
from .views import login_api


app_name = 'users'

urlpatterns = [
    path('request-access/', views.request_access, name='request_access'),
    path('register/<uuid:token>/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('approve/<int:pk>/', views.approve_user, name='approve_user'),
    path('api/login/', login_api, name='api_login'),
]