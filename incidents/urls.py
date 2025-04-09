from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IncidentListView, IncidentDetailView,
    assign_ticket, start_work, pause_work, complete_work, client_response,
    IncidentViewSet, api_assign_ticket, api_start_work, api_pause_work,
    api_complete_work, api_client_response
)

router = DefaultRouter()
router.register(r'api/incidents', IncidentViewSet)

urlpatterns = [
    # HTML-rendering views (browser-based)
    path('', IncidentListView.as_view(), name='incident_list'),
    path('<int:pk>/', IncidentDetailView.as_view(), name='incident_detail'),
    path('ticket/<int:ticket_id>/assign/', assign_ticket, name='assign_ticket'),
    path('ticket/<int:ticket_id>/start/', start_work, name='start_work'),
    path('ticket/<int:ticket_id>/pause/', pause_work, name='pause_work'),
    path('ticket/<int:ticket_id>/complete/', complete_work, name='complete_work'),
    path('<int:incident_id>/client-response/', client_response, name='client_response'),

    # API endpoints (frontend/backend apps)
    path('api/ticket/<int:ticket_id>/assign/', api_assign_ticket, name='api_assign_ticket'),
    path('api/ticket/<int:ticket_id>/start/', api_start_work, name='api_start_work'),
    path('api/ticket/<int:ticket_id>/pause/', api_pause_work, name='api_pause_work'),
    path('api/ticket/<int:ticket_id>/complete/', api_complete_work, name='api_complete_work'),
    path('api/<int:incident_id>/client-response/', api_client_response, name='api_client_response'),

    # DRF router-based endpoints (e.g. /api/incidents/)
    path('', include(router.urls)),
]
