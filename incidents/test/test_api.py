import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from incidents.models import Incident, Ticket
from common.enums import TicketStatus
from users.models import CustomUser, Analyst
from clients.models import Client
from shifts.models import Shift
from rest_framework.authtoken.models import Token
from django.utils import timezone

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def analyst_user():
    user = CustomUser.objects.create_user(username="analyst1", password="testpass123", email="analyst1@ey.com")
    shift = Shift.objects.create(
        start_time=timezone.now() - timezone.timedelta(hours=1),
        end_time=timezone.now() + timezone.timedelta(hours=1),
        name="Test Shift",
        weekday=1
    )
    analyst = Analyst.objects.create(user=user, max_capacity=5, current_shift=shift)
    token = Token.objects.create(user=user)
    return user, analyst, token

@pytest.mark.django_db
def test_incident_list_api(api_client, analyst_user):
    user, _, token = analyst_user
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    client = Client.objects.create(name="Test Client", contact_email="test@client.com")
    Incident.objects.create(client=client, severity="HIGH")
    response = api_client.get('/incidents/api/incidents/')
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['severity'] == "HIGH"

@pytest.mark.django_db
def test_assign_ticket_api(api_client):
    # Create user and token first, without analyst
    user = CustomUser.objects.create_user(username="analyst8", password="testpass123456789", email="analyst1@ey.com")
    token = Token.objects.create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    api_client.force_authenticate(user=user)

    # Create client and incident (ticket created with status 'new', no auto-assignment yet)
    client = Client.objects.create(name="Test Client", contact_email="test@client.com")
    incident = Incident.objects.create(client=client, severity="MEDIUM")
    ticket = incident.ticket
    assert ticket.status == TicketStatus.NEW.value  # Verify ticket is 'new'

    # Now create shift and analyst
    shift = Shift.objects.create(
        start_time=timezone.now() - timezone.timedelta(hours=1),
        end_time=timezone.now() + timezone.timedelta(hours=1),
        name="Test Shift",
        weekday=1
    )
    analyst = Analyst.objects.create(user=user, max_capacity=5, current_shift=shift)

    # Assign ticket via API
    response = api_client.post(f'/incidents/api/ticket/{ticket.id}/assign/')
    assert response.status_code == 200
    ticket.refresh_from_db()
    assert ticket.status == TicketStatus.ASSIGNED.value  # Use enum value

@pytest.mark.django_db
def test_start_work_api(api_client, analyst_user):
    user, analyst, token = analyst_user
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    api_client.force_authenticate(user=user)  # Ensure authentication
    client = Client.objects.create(name="Test Client", contact_email="test@client.com")
    incident = Incident.objects.create(client=client, severity="MEDIUM")
    ticket = incident.ticket
    ticket.assign_to_analyst(analyst)
    response = api_client.post(f'/incidents/api/ticket/{ticket.id}/start/')
    assert response.status_code == 200
    ticket.refresh_from_db()
    assert ticket.status == TicketStatus.IN_PROGRESS.value  # Use enum value