from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=17, blank=True, null=True)  # Optional
    address = models.TextField(blank=True, null=True)  # Optional
    created_at = models.DateTimeField(auto_now_add=True)  # Auto-set on creation
    is_active = models.BooleanField(default=True)  # Active by default

    def __str__(self):
        return self.name

    def get_contact_info(self):
        info = f"Name: {self.name}\nEmail: {self.contact_email}"
        if self.phone_number:
            info += f"\nPhone: {self.phone_number}"
        if self.address:
            info += f"\nAddress: {self.address}"
        return info