from django.urls import path
from .views import (
    IncidentListView, IncidentDetailView,
    assign_ticket, start_work, pause_work, complete_work, client_response
)

urlpatterns = [
    path('', IncidentListView.as_view(), name='incident_list'),
    path('<int:pk>/', IncidentDetailView.as_view(), name='incident_detail'),
    path('ticket/<int:ticket_id>/assign/', assign_ticket, name='assign_ticket'),
    path('ticket/<int:ticket_id>/start/', start_work, name='start_work'),
    path('ticket/<int:ticket_id>/pause/', pause_work, name='pause_work'),
    path('ticket/<int:ticket_id>/complete/', complete_work, name='complete_work'),
    path('<int:incident_id>/client-response/', client_response, name='client_response'),
]