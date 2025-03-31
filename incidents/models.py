from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from users.models import CustomUser, Analyst 
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Enums for status and severity fields
class IncidentStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    ASSIGNED = 'assigned', 'Assigned'
    IN_PROGRESS = 'in_progress', 'In Progress'
    CLOSED = 'closed', 'Closed'

class TicketStatus(models.TextChoices):
    NEW = 'new', 'New'
    ASSIGNED = 'assigned', 'Assigned'
    IN_PROGRESS = 'in_progress', 'In Progress'
    PAUSED = 'paused', 'Paused'
    COMPLETED = 'completed', 'Completed'

class SeverityChoices(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'

# Incident Model
class Incident(models.Model):
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='incidents')
    status = models.CharField(
        max_length=20,
        choices=IncidentStatus.choices,
        default=IncidentStatus.OPEN
    )
    severity = models.CharField(
        max_length=10,
        choices=SeverityChoices.choices,
        default=SeverityChoices.MEDIUM
    )
    incident_type = models.CharField(max_length=100)
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    sla_duration = models.DurationField(null=True, blank=True)
    resolution_confirmed_timestamp = models.DateTimeField(null=True, blank=True, help_text="When client confirms resolution")

    def add_ticket(self, description=''):
        """Create and associate a new ticket with this incident."""
        ticket = Ticket.objects.create(incident=self, description=description)
        return ticket
    
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
        """Assign the incident to an analyst via a ticket."""
        tickets = self.assigned_tickets.filter(status__in=[TicketStatus.NEW, TicketStatus.ASSIGNED])
        if tickets.exists():
            ticket = tickets.first()
            ticket.assign_to_analyst(analyst)
            self.status = IncidentStatus.ASSIGNED
            self.save()
            return ticket
        return None

    def start_analysis(self, ticket):
        """Start analysis on a specific ticket."""
        if ticket.incident == self:
            ticket.start_work()
            self.status = IncidentStatus.IN_PROGRESS
            self.save()

    def add_analysis(self, analyst, notes, ticket):
        """Add analysis to the incident."""
        if ticket.incident == self:
            return Analysis.objects.create(incident=self, analyst=analyst, ticket=ticket, notes=notes)
        return None

    def close(self):
        """Close the incident and set resolution timestamp."""
        self.status = IncidentStatus.CLOSED
        self.resolution_confirmed_timestamp = timezone.now()
        self.save()

    def notify_client(self, message):
        subject = f"Incident {self.id} Update"
        if not self.client.contact_email:
            logger.error(f"No contact email for client {self.client.id}")
            return
        try:
            send_mail(
                subject,
                message,
                'soc@ey.com',
                [self.client.contact_email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send email for Incident {self.id}: {e}")
        self.assigned_tickets.filter(description__icontains='client').update(
            client_notified_timestamp=timezone.now()
        )

    def __str__(self):
        return f"Incident {self.id} - {self.incident_type}"

# Analysis Model
class Analysis(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE,related_name='analyses')
    analyst = models.ForeignKey(Analyst, on_delete=models.CASCADE, related_name='analyses')  # Reference Analyst model
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='analyses')
    notes = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def generate_rapport(self):
        """Generate a report based on analysis notes."""
        return f"Analysis Report for Incident {self.incident.id}\nNotes: {self.notes}\nTimestamp: {self.timestamp}"

    def update_notes(self, new_notes):
        """Update analysis notes."""
        self.notes = new_notes
        self.save()

    def __str__(self):
        return f"Analysis for Incident {self.incident.id}"

# Ticket Model
class Ticket(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='assigned_tickets')
    assigned_analyst = models.ForeignKey(
        Analyst,  # Reference Analyst model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.NEW
    )
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
        """Assign ticket to an analyst."""
        if isinstance(analyst, Analyst) and analyst.can_take_ticket(self.incident.severity):
            self.assigned_analyst = analyst
            self.assignment_timestamp = timezone.now()
            self.status = TicketStatus.ASSIGNED
            self.save()
        else:
            raise ValueError("Analyst cannot take this ticket due to capacity or invalid type.")

    def start_work(self):
        """Start working on the ticket."""
        self.status = TicketStatus.IN_PROGRESS
        self.start_timestamp = timezone.now()
        self.save()

    def pause_work(self):
        """Pause work on the ticket."""
        self.status = TicketStatus.PAUSED
        self.save()

    def complete_work(self):
        """Complete the ticket."""
        self.status = TicketStatus.COMPLETED
        self.completion_timestamp = timezone.now()
        self.save()

    def calculate_sla_remaining(self):
        """Calculate remaining SLA time."""
        if self.deadline_timestamp and self.status != TicketStatus.COMPLETED:
            now = timezone.now()
            remaining = self.deadline_timestamp - now
            self.sla_remaining = remaining if remaining.total_seconds() > 0 else timezone.timedelta(0)
            self.save()
            return self.sla_remaining
        return timezone.timedelta(0)

    def set_client_response(self):
        """Set client response timestamp when client responds."""
        self.client_response_timestamp = timezone.now()
        self.save()

    def __str__(self):
        return f"Ticket {self.id} - {self.status}"

# Metrics Model
class Metrics(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='metrics')
    mtd = models.DurationField(null=True, blank=True, help_text="Mean Time to Detect")
    mta = models.DurationField(null=True, blank=True, help_text="Mean Time to Analyze")
    mtr = models.DurationField(null=True, blank=True, help_text="Mean Time to Respond")
    sla_met = models.BooleanField(default=False)

    def calculate_mtd(self):
        """Calculate Mean Time to Detect."""
        if self.ticket.creation_timestamp and self.ticket.start_timestamp:
            self.mtd = self.ticket.start_timestamp - self.ticket.creation_timestamp
            self.save()

    def calculate_mta(self):
        """Calculate Mean Time to Analyze."""
        if self.ticket.start_timestamp and self.ticket.completion_timestamp:
            self.mta = self.ticket.completion_timestamp - self.ticket.start_timestamp
            self.save()

    def calculate_mtr(self):
        """Calculate Mean Time to Respond."""
        if self.ticket.creation_timestamp and self.ticket.client_response_timestamp:
            self.mtr = self.ticket.client_response_timestamp - self.ticket.creation_timestamp
            self.save()

    def check_sla_met(self):
        """Check if SLA was met."""
        if self.ticket.deadline_timestamp and self.ticket.completion_timestamp:
            self.sla_met = self.ticket.completion_timestamp <= self.ticket.deadline_timestamp
            self.save()
        return self.sla_met

    def __str__(self):
        return f"Metrics for Ticket {self.ticket.id}"

# Signals for automation
@receiver(post_save, sender=Ticket)
def set_deadline_timestamp(sender, instance, created, **kwargs):
    # Only calculate for new tickets
    if created and instance.incident.sla_duration:
        instance.deadline_timestamp = instance.creation_timestamp + instance.incident.sla_duration
        # Save the updated deadline without triggering another full save cycle
        instance.save(update_fields=['deadline_timestamp'])

@receiver(post_save, sender=Ticket)
def update_metrics(sender, instance, created, **kwargs):
    """Update metrics when ticket status changes or client responds."""
    metrics, _ = Metrics.objects.get_or_create(ticket=instance)
    if instance.status == TicketStatus.IN_PROGRESS:
        metrics.calculate_mtd()
    elif instance.status == TicketStatus.COMPLETED:
        metrics.calculate_mta()
        metrics.check_sla_met()
    if instance.client_response_timestamp:
        metrics.calculate_mtr()