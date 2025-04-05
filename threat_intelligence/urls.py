from django.urls import path
from . import views

app_name = 'threat_intel'

urlpatterns = [
    path('iocs/', views.ioc_list, name='ioc_list'),
    path('iocs/<int:ioc_id>/', views.ioc_detail, name='ioc_detail'),
    path('incidents/<int:incident_id>/add-ioc/', views.add_ioc_to_incident, name='add_ioc_to_incident'),
    path('playbooks/', views.playbook_list, name='playbook_list'),
    path('playbooks/<int:playbook_id>/', views.playbook_detail, name='playbook_detail'),
    path('incidents/<int:incident_id>/start-playbook/<int:playbook_id>/', views.start_playbook, name='start_playbook'),
    path('incidents/<int:incident_id>/check-ioc-matches/', views.check_ioc_matches, name='check_ioc_matches'),
    path('pause-playbook/<int:execution_id>/', views.pause_playbook, name='pause_playbook'),
]