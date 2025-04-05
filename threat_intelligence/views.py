from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import IOC, Playbook, PlaybookExecution,PlaybookStepExecution
from incidents.models import Incident, Analysis, Ticket
import json

@login_required
def ioc_list(request):
    iocs = IOC.objects.all().order_by('-created_at')
    return render(request, 'threat_intelligence/ioc_list.html', {'iocs': iocs})

@login_required
def ioc_detail(request, ioc_id):
    ioc = get_object_or_404(IOC, pk=ioc_id)
    return render(request, 'threat_intelligence/ioc_detail.html', {'ioc': ioc})

@login_required
def add_ioc_to_incident(request, incident_id):
    if request.method == 'POST':
        incident = get_object_or_404(Incident, pk=incident_id)
        ioc_type = request.POST.get('type')
        ioc_value = request.POST.get('value')
        source = request.POST.get('source', 'internal')
        if not IOC.objects.filter(type=ioc_type, value=ioc_value).exists():
            ioc = incident.add_ioc(ioc_type, ioc_value, source)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'ioc_id': ioc.id})
        else:
            return JsonResponse({'success': False, 'error': 'IOC already exists'})
    return redirect('incident_detail', pk=incident_id)

@login_required
def playbook_list(request):
    playbooks = Playbook.objects.all()
    return render(request, 'threat_intelligence/playbook_list.html', {'playbooks': playbooks})

@login_required
def playbook_detail(request, playbook_id):
    playbook = get_object_or_404(Playbook, pk=playbook_id)
    return render(request, 'threat_intelligence/playbook_detail.html', {'playbook': playbook})

@login_required
def start_playbook(request, incident_id, playbook_id):
    if request.method == 'POST':
        incident = get_object_or_404(Incident, pk=incident_id)
        playbook = get_object_or_404(Playbook, pk=playbook_id)
        ticket_id = request.POST.get('ticket_id')
        analysis_id = request.POST.get('analysis_id')
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        analysis = get_object_or_404(Analysis, pk=analysis_id)
        
        if not incident.playbook_executions.filter(playbook=playbook, status__in=['in_progress', 'paused']).exists(): 
            execution = incident.start_playbook(playbook, ticket, analysis)
            for step in playbook.steps.all():
                PlaybookStepExecution.objects.create(playbook_execution=execution, step=step).execute()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'execution_id': execution.id})
        else:
            return JsonResponse({'success': False, 'error': 'Playbook already running'})
    return redirect('incident_detail', pk=incident_id)

@login_required
def check_ioc_matches(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    match_score = incident.check_iocs_against_db()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'match_score': match_score})
    
    return redirect('incident_detail', pk=incident_id)

@login_required
def pause_playbook(request, execution_id):
    execution = get_object_or_404(PlaybookExecution, id=execution_id)
    if request.method == 'POST':
        execution.pause()
        return JsonResponse({'success': True})
    return redirect('incident_detail', pk=execution.incident.id)