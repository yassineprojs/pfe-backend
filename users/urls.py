from django.urls import path
from . import views
from .views import login_api


app_name = 'users'

urlpatterns = [
    path('api/request-access/', views.request_access_api, name='request_access_api'),
    path('api/register/<uuid:token>/', views.register_api, name='register_api'),
    # path('login/', views.login_view, name='login'),  # Optional: Keep if using Django's login page
    # path('logout/', views.logout_view, name='logout'),
    path('approve/<int:pk>/', views.approve_user, name='approve_user'),
    path('api/login/', login_api, name='api_login'),
    path('api/logout/', views.logout_api, name='api_logout'),
]