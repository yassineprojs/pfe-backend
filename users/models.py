from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from common.enums import TicketStatus
import uuid


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{8,15}$', message="Phone number must be entered in the format: '+99999999'.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

class Analyst(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    current_shift = models.ForeignKey('shifts.Shift', on_delete=models.SET_NULL, null=True, blank=True, related_name='analysts')
    max_capacity = models.PositiveIntegerField(default=5)

    @property
    def current_workload(self):
        return self.assigned_tickets.filter(
            status__in=[TicketStatus.NEW, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS]
        ).count()

    def can_take_ticket(self, severity):
        return self.current_workload < self.max_capacity

    def __str__(self):
        return f"Analyst: {self.user.get_full_name()}"

class Admin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return f"Admin: {self.user.get_full_name()}"
    
class PendingUser(models.Model):
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=[('Analyst', 'Analyst'), ('Admin', 'Admin')], default='Analyst')

    def __str__(self):
        return self.email