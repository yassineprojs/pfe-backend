from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser, Analyst
import logging
from common.enums import IncidentStatus, TicketStatus, SeverityChoices

logger = logging.getLogger(__name__)


class Incident(models.Model):
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='incidents')
    status = models.CharField(max_length=20, choices=IncidentStatus.choices, default=IncidentStatus.OPEN)
    severity = models.CharField(max_length=10, choices=SeverityChoices.choices, default=SeverityChoices.MEDIUM)
    incident_type = models.CharField(max_length=100, blank=True)
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    sla_duration = models.DurationField(null=True, blank=True)
    resolution_confirmed_timestamp = models.DateTimeField(null=True, blank=True)
    iocs = models.ManyToManyField('threat_intelligence.IOC', through='IncidentIOC', related_name='incidents')

    def save(self, *args, **kwargs):
        sla_map = {
            SeverityChoices.LOW: timezone.timedelta(hours=24),
            SeverityChoices.MEDIUM: timezone.timedelta(hours=12),
            SeverityChoices.HIGH: timezone.timedelta(hours=4),
        }
        if not self.pk:  # New instance
            if not self.sla_duration:
                self.sla_duration = sla_map.get(self.severity, timezone.timedelta(hours=24))
        else:  # Existing instance
            original = Incident.objects.get(pk=self.pk)
            if original.severity != self.severity and original.sla_duration == sla_map.get(original.severity):
                self.sla_duration = sla_map.get(self.severity, timezone.timedelta(hours=24))
        super().save(*args, **kwargs)

    def assign_to_analyst(self, analyst):
        if self.ticket and self.ticket.status in [TicketStatus.NEW, TicketStatus.ASSIGNED]:
            self.ticket.assign_to_analyst(analyst)
            self.status = IncidentStatus.ASSIGNED.value
            self.save()
            return self.ticket
        return None

    def start_analysis(self):
        if self.ticket:
            self.ticket.start_work()
            self.status = IncidentStatus.IN_PROGRESS.value
            self.save()

    def add_analysis(self, analyst, notes):
        if self.ticket:
            return Analysis.objects.create(
                incident=self,
                analyst=analyst,
                ticket=self.ticket,
                notes=notes
            )
        return None

    def update_status(self):
        if not self.ticket:
            self.status = IncidentStatus.OPEN
        elif self.ticket.status == TicketStatus.COMPLETED and self.ticket.client_response_timestamp:
            self.status = IncidentStatus.CLOSED
            self.resolution_confirmed_timestamp = timezone.now()
        else:
            self.status = self.ticket.status
        self.save()

    def close(self):
        if self.ticket and self.ticket.status == TicketStatus.COMPLETED:
            self.status = IncidentStatus.CLOSED
            self.resolution_confirmed_timestamp = timezone.now()
            self.save()

    def notify_client(self, message):
        subject = f"Incident {self.id} Update"
        if not self.client or not self.client.contact_email:
            logger.error(f"No contact email for client {self.client.id if self.client else 'Unknown'}")
            return
        try:
            send_mail(subject, message, 'soc@ey.com', [self.client.contact_email], fail_silently=False)
            if self.ticket and 'client' in self.ticket.description.lower():
                self.ticket.client_notified_timestamp = timezone.now()
                self.ticket.save()
        except Exception as e:
            logger.error(f"Failed to send email for Incident {self.id}: {e}")

    def add_ioc(self, ioc_type, ioc_value, source=None):
        from threat_intelligence.models import IOC  # Lazy import inside method
        source = source or 'internal'
        ioc, created = IOC.objects.get_or_create(
            type=ioc_type,
            value=ioc_value,
            defaults={'source': source}
        )
        IncidentIOC.objects.get_or_create(incident=self, ioc=ioc)
        match_score = self.check_iocs_against_db()
        if match_score > 50:  # Adjust severity based on matches
            if self.severity == SeverityChoices.LOW:
                self.severity = SeverityChoices.MEDIUM
            elif self.severity == SeverityChoices.MEDIUM:
                self.severity = SeverityChoices.HIGH
            self.save()
        return ioc

    def check_iocs_against_db(self):
        incident_iocs = self.iocs.all()
        if not incident_iocs:
            return 0
        match_score = 0
        for ioc in incident_iocs:
            other_incidents_count = IncidentIOC.objects.filter(ioc=ioc).exclude(incident=self).count()
            if other_incidents_count > 0:
                match_score += 1
        return (match_score / incident_iocs.count()) * 100 if incident_iocs.count() > 0 else 0

    def start_playbook(self, playbook, ticket, analysis):
        if ticket.incident != self:
            raise ValueError("Ticket does not belong to this incident")
        from threat_intelligence.models import PlaybookExecution  # Lazy import inside method
        execution = PlaybookExecution.objects.create(
            playbook=playbook,
            incident=self,
            ticket=ticket,
            analysis=analysis
        )
        execution.execute()
        return execution

    def __str__(self):
        return f"Incident {self.id} - {self.incident_type}"

class IncidentIOC(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    ioc = models.ForeignKey('threat_intelligence.IOC', on_delete=models.CASCADE) 
    class Meta:
        unique_together = ['incident', 'ioc']

class Analysis(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='analyses')
    analyst = models.ForeignKey(Analyst, on_delete=models.CASCADE, related_name='analyses')
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='analyses')
    notes = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def generate_rapport(self):
        return f"Analysis Report for Incident {self.incident.id}\nNotes: {self.notes}\nTimestamp: {self.timestamp}"

    def update_notes(self, new_notes):
        self.notes = new_notes
        self.save()

    def __str__(self):
        return f"Analysis for Incident {self.incident.id}"

class Ticket(models.Model):
    incident = models.OneToOneField(Incident, on_delete=models.CASCADE, related_name='ticket')
    assigned_analysts = models.ManyToManyField(Analyst, related_name='assigned_tickets', blank=True)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.NEW)
    description = models.TextField(blank=True)
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    assignment_timestamp = models.DateTimeField(null=True, blank=True)
    start_timestamp = models.DateTimeField(null=True, blank=True)
    completion_timestamp = models.DateTimeField(null=True, blank=True)
    sla_remaining = models.DurationField(null=True, blank=True)
    deadline_timestamp = models.DateTimeField(null=True, blank=True)
    client_notified_timestamp = models.DateTimeField(null=True, blank=True)
    client_response_timestamp = models.DateTimeField(null=True, blank=True)

    def assign_to_analyst(self, analyst):
        if isinstance(analyst, Analyst) and analyst.can_take_ticket(self.incident.severity):
            self.assigned_analysts.add(analyst)
            self.assignment_timestamp = timezone.now()
            self.status = TicketStatus.ASSIGNED
            self.save()
        else:
            raise ValueError("Analyst cannot take this ticket due to capacity or invalid type.")

    def start_work(self):
        self.status = TicketStatus.IN_PROGRESS
        self.start_timestamp = timezone.now()
        self.save()

    def pause_work(self):
        self.status = TicketStatus.PAUSED
        self.save()

    def complete_work(self):
        self.status = TicketStatus.COMPLETED
        self.completion_timestamp = timezone.now()
        self.save()

    def calculate_sla_remaining(self):
        if self.deadline_timestamp and self.status != TicketStatus.COMPLETED:
            now = timezone.now()
            remaining = self.deadline_timestamp - now
            self.sla_remaining = remaining if remaining.total_seconds() > 0 else timezone.timedelta(0)
            self.save()
            return self.sla_remaining
        return timezone.timedelta(0)

    def set_client_response(self):
        self.client_response_timestamp = timezone.now()
        self.save()

    def __str__(self):
        return f"Ticket {self.id} - {self.status}"

class Metrics(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='metrics')
    mtd = models.DurationField(null=True, blank=True, help_text="Mean Time to Detect")
    mta = models.DurationField(null=True, blank=True, help_text="Mean Time to Analyze")
    mtr = models.DurationField(null=True, blank=True, help_text="Mean Time to Respond")
    sla_met = models.BooleanField(default=False)

    def calculate_mtd(self):
        if self.ticket.creation_timestamp and self.ticket.start_timestamp:
            self.mtd = self.ticket.start_timestamp - self.ticket.creation_timestamp
            self.save()

    def calculate_mta(self):
        if self.ticket.start_timestamp and self.ticket.completion_timestamp:
            self.mta = self.ticket.completion_timestamp - self.ticket.start_timestamp
            self.save()

    def calculate_mtr(self):
        if self.ticket.creation_timestamp and self.ticket.client_response_timestamp:
            self.mtr = self.ticket.client_response_timestamp - self.ticket.creation_timestamp
            self.save()

    def check_sla_met(self):
        if self.ticket.deadline_timestamp and self.ticket.completion_timestamp:
            self.sla_met = self.ticket.completion_timestamp <= self.ticket.deadline_timestamp
            self.save()
        return self.sla_met

    def __str__(self):
        return f"Metrics for Ticket {self.ticket.id}"

@receiver(post_save, sender=Incident)
def create_ticket(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'ticket'):
        ticket = Ticket.objects.create(incident=instance)
        assign_ticket_to_analyst(ticket)  # Auto-assign

@receiver(post_save, sender=Ticket)
def set_deadline_timestamp(sender, instance, created, **kwargs):
    if created and instance.incident.sla_duration:
        instance.deadline_timestamp = instance.creation_timestamp + instance.incident.sla_duration
        instance.save(update_fields=['deadline_timestamp'])

@receiver(post_save, sender=Ticket)
def update_metrics(sender, instance, created, **kwargs):
    metrics, _ = Metrics.objects.get_or_create(ticket=instance)
    if instance.status == TicketStatus.IN_PROGRESS:
        metrics.calculate_mtd()
    elif instance.status == TicketStatus.COMPLETED:
        metrics.calculate_mta()
        metrics.check_sla_met()
    if instance.client_response_timestamp:
        metrics.calculate_mtr()

def assign_ticket_to_analyst(ticket):
    current_time = timezone.now()
    # Get analysts in the current shift
    analysts_in_shift = Analyst.objects.filter(
        current_shift__start_time__lte=current_time,
        current_shift__end_time__gte=current_time
    )
    if not analysts_in_shift.exists():
        return None

    # Compute workload in Python and find an available analyst
    available_analysts = [
        analyst for analyst in analysts_in_shift
        if analyst.current_workload < analyst.max_capacity
    ]
    if not available_analysts:
        return None

    # Sort by workload and pick the analyst with the least
    analyst = min(available_analysts, key=lambda a: a.current_workload)
    ticket.assign_to_analyst(analyst)
    return analyst