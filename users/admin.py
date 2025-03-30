# users/admin.py
from django.contrib import admin
from .models import CustomUser, Analyst, Admin

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number')

@admin.register(Analyst)
class AnalystAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_shift', 'current_workload')

@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ('user', 'permissions')
