import pytest
from django.utils import timezone
from incidents.models import Incident, Ticket, Analysis, Metrics
from users.models import CustomUser, Analyst
from clients.models import Client
from shifts.models import Shift  # Assuming this exists
from common.enums import IncidentStatus, TicketStatus, SeverityChoices

@pytest.mark.django_db
def test_incident_creation():
    client = Client.objects.create(name="Test Client", contact_email="test@client.com")
    incident = Incident.objects.create(client=client, severity=SeverityChoices.HIGH)
    assert incident.status == IncidentStatus.OPEN
    assert incident.sla_duration == timezone.timedelta(hours=4)
    assert incident.ticket is not None
    assert incident.ticket.status == TicketStatus.NEW

@pytest.mark.django_db
def test_ticket_assignment():
    client = Client.objects.create(name="Test Client", contact_email="test@client.com")
    shift = Shift.objects.create(
        start_time=timezone.now() - timezone.timedelta(hours=1),
        end_time=timezone.now() + timezone.timedelta(hours=1),
        name="Test Shift",
        weekday=1 
    )
    incident = Incident.objects.create(client=client, severity=SeverityChoices.MEDIUM)
    user = CustomUser.objects.create(username="analyst1", email="analyst1@ey.com")
    analyst = Analyst.objects.create(user=user, max_capacity=5, current_shift=shift)
    ticket = incident.ticket
    ticket.assign_to_analyst(analyst)
    assert analyst in ticket.assigned_analysts.all()
    assert ticket.status == TicketStatus.ASSIGNED
    assert ticket.assignment_timestamp is not None

@pytest.mark.django_db
def test_analysis_creation():
    client = Client.objects.create(name="Test Client", contact_email="test@client.com")
    shift = Shift.objects.create(
        start_time=timezone.now() - timezone.timedelta(hours=1),
        end_time=timezone.now() + timezone.timedelta(hours=1),
        name="Test Shift",
        weekday=1 
    )
    incident = Incident.objects.create(client=client, severity=SeverityChoices.LOW)
    user = CustomUser.objects.create(username="analyst1", email="analyst1@ey.com")
    analyst = Analyst.objects.create(user=user, current_shift=shift)
    ticket = incident.ticket
    analysis = incident.add_analysis(analyst, "Test notes")
    assert analysis.notes == "Test notes"
    assert analysis.incident == incident
    assert analysis.analyst == analyst

@pytest.mark.django_db
def test_metrics_calculation():
    client = Client.objects.create(name="Test Client", contact_email="test@client.com")
    incident = Incident.objects.create(client=client, severity=SeverityChoices.MEDIUM)
    ticket = incident.ticket
    ticket.start_timestamp = timezone.now()
    ticket.completion_timestamp = ticket.start_timestamp + timezone.timedelta(hours=1)
    ticket.save()
    metrics = Metrics.objects.get(ticket=ticket)
    metrics.calculate_mta()
    assert metrics.mta == timezone.timedelta(hours=1)