# threat_intelligence/models.py
from django.db import models
from django.utils import timezone
from common.enums import PlaybookStatus, IOCTypeChoices, IOCSourceChoices

class IOC(models.Model):
    type = models.CharField(max_length=20, choices=IOCTypeChoices.choices)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=20, choices=IOCSourceChoices.choices, default=IOCSourceChoices.INTERNAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confidence_score = models.IntegerField(default=50)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        unique_together = ['type', 'value']
        indexes = [models.Index(fields=['type', 'value']), models.Index(fields=['value'])]

    def check_against_threat_intel(self):
        # Placeholder for external API integration (e.g., VirusTotal)
        return False

    def __str__(self):
        return f"{self.type}: {self.value}"

class Playbook(models.Model):
    playbook_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    incident_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PlaybookStep(models.Model):
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveIntegerField()
    description = models.TextField()
    is_automated = models.BooleanField(default=False)
    automation_script = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['step_number']

    def __str__(self):
        return f"{self.playbook.name} - Step {self.step_number}"

class PlaybookExecution(models.Model):
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, related_name='executions')
    incident = models.ForeignKey('incidents.Incident', on_delete=models.CASCADE, related_name='playbook_executions')  
    ticket = models.ForeignKey('incidents.Ticket', on_delete=models.CASCADE, related_name='playbook_executions')  
    analysis = models.ForeignKey('incidents.Analysis', on_delete=models.CASCADE, related_name='playbook_executions')  
    status = models.CharField(max_length=20, choices=PlaybookStatus.choices, default=PlaybookStatus.NOT_STARTED)
    start_time = models.DateTimeField(null=True, blank=True)
    pause_time = models.DateTimeField(null=True, blank=True)
    total_paused_time = models.DurationField(default=timezone.timedelta(0))
    completion_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def execute(self):
        if self.status == PlaybookStatus.NOT_STARTED:
            self.start_time = timezone.now()
        elif self.status == PlaybookStatus.PAUSED:
            pass
        self.status = PlaybookStatus.IN_PROGRESS
        self.save()

    def pause(self):
        if self.status == PlaybookStatus.IN_PROGRESS:
            self.status = PlaybookStatus.PAUSED
            self.pause_time = timezone.now()
            self.save()

    def resume(self):
        if self.status == PlaybookStatus.PAUSED and self.pause_time:
            paused_duration = timezone.now() - self.pause_time
            self.total_paused_time += paused_duration
            self.status = PlaybookStatus.IN_PROGRESS
            self.pause_time = None
            self.save()

    def complete(self):
        self.status = PlaybookStatus.COMPLETED
        self.completion_time = timezone.now()
        self.save()

    def get_execution_time(self):
        if not self.start_time:
            return timezone.timedelta(0)
        end_time = self.completion_time or timezone.now()
        active_time = end_time - self.start_time - self.total_paused_time
        return active_time if active_time.total_seconds() > 0 else timezone.timedelta(0)

    def __str__(self):
        return f"Execution of {self.playbook.name} for Incident {self.incident.id}"

class PlaybookStepExecution(models.Model):
    playbook_execution = models.ForeignKey(PlaybookExecution, on_delete=models.CASCADE, related_name='step_executions')
    step = models.ForeignKey(PlaybookStep, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=PlaybookStatus.choices, default=PlaybookStatus.NOT_STARTED)
    start_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    result = models.TextField(blank=True)

    class Meta:
        ordering = ['step__step_number']

    def execute(self):
        self.status = PlaybookStatus.IN_PROGRESS
        self.start_time = timezone.now()
        self.save()
        if self.step.is_automated:
            # Implement automation logic here
            pass

    def complete(self, result=''):
        self.status = PlaybookStatus.COMPLETED
        self.completion_time = timezone.now()
        self.result = result
        self.save()

    def __str__(self):
        return f"Step {self.step.step_number} of {self.playbook_execution}"