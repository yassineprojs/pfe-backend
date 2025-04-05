from django.db import models

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

class IOCSourceChoices(models.TextChoices):
    INTERNAL = 'internal', 'Internal'
    EXTERNAL = 'external', 'External'

class IOCTypeChoices(models.TextChoices):
    IP = 'ip', 'IP Address'
    EMAIL = 'email', 'Email Address'
    DOMAIN = 'domain', 'Domain'
    URL = 'url', 'URL'
    HASH = 'hash', 'File Hash'
    SUBJECT = 'subject', 'Email Subject'
    OTHER = 'other', 'Other'

class PlaybookStatus(models.TextChoices):
    NOT_STARTED = 'not_started', 'Not Started'
    IN_PROGRESS = 'in_progress', 'In Progress'
    PAUSED = 'paused', 'Paused'
    COMPLETED = 'completed', 'Completed'