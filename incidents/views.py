from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Incident, Ticket, Analysis, IncidentStatus, TicketStatus
from threat_intelligence.models import Playbook
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import IncidentSerializer
from django.shortcuts import get_object_or_404

class IncidentListView(LoginRequiredMixin, ListView):
    model = Incident
    template_name = 'incidents/incident_list.html'
    context_object_name = 'incidents'

    def get_queryset(self):
        queryset = Incident.objects.filter(
            status__in=[IncidentStatus.OPEN, IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS]
        )
        status = self.request.GET.get('status')
        severity = self.request.GET.get('severity')
        analyst = self.request.GET.get('analyst')
        if status:
            queryset = queryset.filter(status=status)
        if severity:
            queryset = queryset.filter(severity=severity)
        if analyst:
            queryset = queryset.filter(ticket__assigned_analysts__user__username=analyst)
        return queryset.distinct()

class IncidentDetailView(LoginRequiredMixin, DetailView):
    model = Incident
    template_name = 'incidents/incident_detail.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ticket'] = self.object.ticket
        context['analyses'] = self.object.analyses.all()
        if self.object.ticket:
            context['sla_remaining'] = self.object.ticket.calculate_sla_remaining()
        return context

def assign_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if (ticket.status == TicketStatus.NEW and 
        hasattr(request.user, 'analyst') and 
        request.user.analyst.can_take_ticket(ticket.incident.severity)):
        ticket.assign_to_analyst(request.user.analyst)
        messages.success(request, "Ticket assigned successfully.")
    else:
        messages.error(request, "Cannot assign this ticket.")
    return redirect('incident_detail', pk=ticket.incident.id)

def start_work(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if (request.user.analyst in ticket.assigned_analysts.all() and 
        ticket.status == TicketStatus.ASSIGNED):
        ticket.start_work()
        ticket.incident.status = IncidentStatus.IN_PROGRESS
        ticket.incident.save()
        messages.success(request, "Work started on ticket.")
    else:
        messages.error(request, "Cannot start work on this ticket.")
    return redirect('incident_detail', pk=ticket.incident.id)

def pause_work(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if (request.user.analyst in ticket.assigned_analysts.all() and 
        ticket.status == TicketStatus.IN_PROGRESS):
        ticket.pause_work()
        messages.success(request, "Work paused.")
    else:
        messages.error(request, "Cannot pause this ticket.")
    return redirect('incident_detail', pk=ticket.incident.id)

def complete_work(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST' and request.user.analyst in ticket.assigned_analysts.all():
        classification = request.POST.get('classification')
        notes = request.POST.get('notes', '')
        ticket.incident.incident_type = classification
        analysis = ticket.incident.add_analysis(request.user.analyst, notes)
        ticket.complete_work()
        if classification in ['true_positive_legitimate', 'true_positive_phishing']:
            try:
                playbook = Playbook.objects.get(incident_type=classification)
                ticket.incident.start_playbook(playbook, ticket, analysis)
            except Playbook.DoesNotExist:
                messages.error(request, "No playbook found for this incident type.")
            message = f"Incident classified as {classification}. Recommended action: {request.POST.get('action', 'Review')}"
            ticket.incident.notify_client(message)
        else:
            ticket.incident.close()
        messages.success(request, "Ticket completed.")
    else:
        messages.error(request, "Cannot complete this ticket.")
    return redirect('incident_detail', pk=ticket.incident.id)

def client_response(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    if request.method == 'POST':
        ticket = incident.ticket
        ticket.set_client_response()
        incident.update_status()
        messages.success(request, "Client response recorded.")
    return redirect('incident_detail', pk=incident_id)


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')
        analyst = self.request.query_params.get('analyst')
        if status:
            queryset = queryset.filter(status=status)
        if severity:
            queryset = queryset.filter(severity=severity)
        if analyst:
            queryset = queryset.filter(ticket__assigned_analysts__user__username=analyst)
        return queryset.distinct()

# API endpoints for ticket actions
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_assign_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if (ticket.status == TicketStatus.NEW and 
        hasattr(request.user, 'analyst') and 
        request.user.analyst.can_take_ticket(ticket.incident.severity)):
        ticket.assign_to_analyst(request.user.analyst)
        return Response({'status': 'Ticket assigned successfully.'})
    return Response({'error': 'Cannot assign this ticket.'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_start_work(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if (request.user.analyst in ticket.assigned_analysts.all() and 
        ticket.status == TicketStatus.ASSIGNED):
        ticket.start_work()
        ticket.incident.status = IncidentStatus.IN_PROGRESS
        ticket.incident.save()
        return Response({'status': 'Work started on ticket.'})
    return Response({'error': 'Cannot start work on this ticket.'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_pause_work(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if (request.user.analyst in ticket.assigned_analysts.all() and 
        ticket.status == TicketStatus.IN_PROGRESS):
        ticket.pause_work()
        return Response({'status': 'Work paused.'})
    return Response({'error': 'Cannot pause this ticket.'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_complete_work(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.user.analyst in ticket.assigned_analysts.all():
        classification = request.data.get('classification')
        notes = request.data.get('notes', '')
        ticket.incident.incident_type = classification
        analysis = ticket.incident.add_analysis(request.user.analyst, notes)
        ticket.complete_work()
        if classification in ['true_positive_legitimate', 'true_positive_phishing']:
            try:
                from threat_intelligence.models import Playbook
                playbook = Playbook.objects.get(incident_type=classification)
                ticket.incident.start_playbook(playbook, ticket, analysis)
            except Playbook.DoesNotExist:
                return Response({'error': 'No playbook found for this incident type.'}, status=400)
            message = f"Incident classified as {classification}. Recommended action: Review"
            ticket.incident.notify_client(message)
        else:
            ticket.incident.close()
        return Response({'status': 'Ticket completed.'})
    return Response({'error': 'Cannot complete this ticket.'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_client_response(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    ticket = incident.ticket
    ticket.set_client_response()
    incident.update_status()
    return Response({'status': 'Client response recorded.'})