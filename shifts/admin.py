# shifts/admin.py
from django.contrib import admin
from .models import Shift, Planning

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'weekday')

@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ('analyst', 'shift', 'plan_date')
    list_filter = ('plan_date', 'shift__name')