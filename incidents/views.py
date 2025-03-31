from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from .models import Incident, Ticket, Analysis, IncidentStatus, TicketStatus
from django.contrib import messages
from django.utils import timezone

class IncidentListView(LoginRequiredMixin, ListView):
    model = Incident
    template_name = 'incidents/incident_list.html'
    context_object_name = 'incidents'

    def get_queryset(self):
        """
        Filter incidents based on status and query parameters.
        Only show open, assigned, or in-progress incidents by default.
        """
        # Use IncidentStatus enum values for filtering
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
            # Correct filter assuming Analyst has a user field with username
            queryset = queryset.filter(ticket__assigned_analyst__user__username=analyst)
        return queryset.distinct()

class IncidentDetailView(LoginRequiredMixin, DetailView):
    model = Incident
    template_name = 'incidents/incident_detail.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        """Add tickets, analyses, and SLA remaining to the context."""
        context = super().get_context_data(**kwargs)
        # Use correct related_name from models.py
        context['tickets'] = self.object.assigned_tickets.all()
        context['analyses'] = self.object.analyses.all()
        if context['tickets']:
            context['sla_remaining'] = context['tickets'].first().calculate_sla_remaining()
        return context

def assign_ticket(request, ticket_id):
    """Assign a ticket to the current user's analyst instance."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if ticket.status == TicketStatus.NEW and hasattr(request.user, 'analyst'):
        # Use request.user.analyst instead of request.user
        ticket.assign_to_analyst(request.user.analyst)
        messages.success(request, "Ticket assigned successfully.")
    else:
        messages.error(request, "Cannot assign this ticket.")
    return redirect('incident_detail', pk=ticket.incident.id)

def start_work(request, ticket_id):
    """Start work on a ticket if assigned to the current analyst."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if ticket.assigned_analyst == request.user.analyst and ticket.status == TicketStatus.ASSIGNED:
        ticket.incident.start_analysis(ticket)
        messages.success(request, "Work started on ticket.")
    else:
        messages.error(request, "Cannot start work on this ticket.")
    return redirect('incident_detail', pk=ticket.incident.id)

def pause_work(request, ticket_id):
    """Pause work on a ticket if in progress and assigned to the current analyst."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if ticket.assigned_analyst == request.user.analyst and ticket.status == TicketStatus.IN_PROGRESS:
        ticket.pause_work()
        messages.success(request, "Work paused.")
    else:
        messages.error(request, "Cannot pause this ticket.")
    return redirect('incident_detail', pk=ticket.incident.id)

def complete_work(request, ticket_id):
    """Complete a ticket, classify the incident, and handle resolution."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'POST' and ticket.assigned_analyst == request.user.analyst:
        classification = request.POST.get('classification')
        notes = request.POST.get('notes', '')
        ticket.incident.incident_type = classification
        # Use request.user.analyst for analysis
        ticket.incident.add_analysis(request.user.analyst, notes, ticket)
        ticket.complete_work()
        if classification in ['true_positive_legitimate', 'true_positive_phishing']:
            message = f"Incident classified as {classification}. Recommended action: {request.POST.get('action', 'Review')}"
            ticket.incident.notify_client(message)
        else:
            ticket.incident.close()  # False positives close immediately
        messages.success(request, "Ticket completed.")
    else:
        messages.error(request, "Cannot complete this ticket.")
    return redirect('incident_detail', pk=ticket.incident.id)

def client_response(request, incident_id):
    """Handle client response to close the incident."""
    incident = get_object_or_404(Incident, id=incident_id)
    if request.method == 'POST':
        # Use correct related_name 'assigned_tickets'
        for ticket in incident.assigned_tickets.all():
            ticket.client_response_timestamp = timezone.now()
            ticket.save()  # Triggers MTR calculation via signals
        incident.close()
        messages.success(request, "Incident closed based on client response.")
    # Corrected: Removed trailing comma
    return redirect('incident_list')