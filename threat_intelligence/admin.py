# threat_intelligence/admin.py
from django.contrib import admin
from .models import IOC, Playbook, PlaybookExecution, PlaybookStepExecution

@admin.register(IOC)
class IOCAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'value', 'source','description', 'created_at', 'is_blocked')  
    list_filter = ('type', 'source', 'is_blocked')  
    search_fields = ('value',)
    readonly_fields = ('created_at', 'updated_at')  

@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    list_display = ('playbook_id', 'name', 'incident_type', 'created_at')
    list_filter = ('incident_type',)
    search_fields = ('name', 'description', 'incident_type')

@admin.register(PlaybookExecution)
class PlaybookExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'playbook', 'incident', 'status', 'start_time', 'completion_time')  
    list_filter = ('status',)
    search_fields = ('playbook__name', 'incident__id', 'notes')

@admin.register(PlaybookStepExecution)
class PlaybookStepExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'playbook_execution', 'step', 'status', 'start_time', 'completion_time')
    list_filter = ('status',)
    search_fields = ('playbook_execution__playbook__name', 'step__description')