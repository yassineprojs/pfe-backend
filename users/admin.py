from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Analyst, Admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib.auth.models import Group


admin.site.unregister(Group)


# Inline for Analyst profile
class AnalystInline(admin.StackedInline):
    model = Analyst
    can_delete = False  # Prevent deleting the profile separately
    extra = 0  # Show only if adding a new user

# Inline for Admin profile
class AdminInline(admin.StackedInline):
    model = Admin
    can_delete = False
    extra = 0

# Custom admin for CustomUser
class CustomUserAdmin(BaseUserAdmin):
    # Fields when editing a user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Status', {'fields': ('is_staff', 'is_active')}),
        ('Dates', {'fields': ('date_joined',)}),
    )
    # Fields when adding a user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone_number', 'is_staff', 'is_active')}
        ),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'get_profile_link')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    inlines = [AnalystInline, AdminInline]  # Show both inlines

    def get_profile_link(self, obj):
        if hasattr(obj, 'analyst'):
            url = reverse("admin:users_analyst_change", args=[obj.analyst.pk])
            return mark_safe(f'<a href="{url}">Analyst Profile</a>')
        elif hasattr(obj, 'admin'):
            url = reverse("admin:users_admin_change", args=[obj.admin.pk])
            return mark_safe(f'<a href="{url}">Admin Profile</a>')
        return "No Profile"
    get_profile_link.short_description = 'Profile'

# Analyst admin
@admin.register(Analyst)
class AnalystAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email', 'current_shift', 'max_capacity')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'

    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'

# Admin admin
@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'

    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'

admin.site.register(CustomUser, CustomUserAdmin)