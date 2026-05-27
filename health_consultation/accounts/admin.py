from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ResidentProfile, HealthWorkerProfile


class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined', 'is_available')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'address', 'profile_picture')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Health Worker Info', {'fields': ('license_number', 'specialization', 'is_available')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'last_updated')


@admin.register(ResidentProfile)
class ResidentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'civil_status', 'created_at')
    list_filter = ('gender', 'civil_status', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)


@admin.register(HealthWorkerProfile)
class HealthWorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'specialization', 'is_on_duty', 'consultation_count', 'created_at')
    list_filter = ('specialization', 'is_on_duty', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'employee_id', 'license_number')
    raw_id_fields = ('user',)
    
    actions = ['set_on_duty', 'set_off_duty']
    
    def set_on_duty(self, request, queryset):
        queryset.update(is_on_duty=True)
    set_on_duty.short_description = "Set selected workers as On Duty"
    
    def set_off_duty(self, request, queryset):
        queryset.update(is_on_duty=False)
    set_off_duty.short_description = "Set selected workers as Off Duty"


# Register the User model
admin.site.register(User, UserAdmin)
