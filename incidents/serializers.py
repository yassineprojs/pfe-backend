from rest_framework import serializers
from .models import Incident, Ticket, Analysis
from common.enums import IncidentStatus, TicketStatus, SeverityChoices

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            'id', 'status', 'description', 'creation_timestamp', 'assignment_timestamp',
            'start_timestamp', 'completion_timestamp', 'sla_remaining', 'deadline_timestamp',
            'client_notified_timestamp', 'client_response_timestamp', 'assigned_analysts'
        ]
        read_only_fields = ['assigned_analysts']

class AnalysisSerializer(serializers.ModelSerializer):
    analyst = serializers.StringRelatedField()  # Display analyst's username or string representation

    class Meta:
        model = Analysis
        fields = ['id', 'analyst', 'notes', 'timestamp']

class IncidentSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)
    analyses = AnalysisSerializer(many=True, read_only=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'client', 'status', 'severity', 'incident_type', 'creation_timestamp',
            'sla_duration', 'resolution_confirmed_timestamp', 'ticket', 'analyses'
        ]