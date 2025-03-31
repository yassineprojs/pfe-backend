from django.contrib import admin
from .models import Incident, Ticket  # Import your Incident model (adjust if named differently)

admin.site.register(Incident)
admin.site.register(Ticket)

