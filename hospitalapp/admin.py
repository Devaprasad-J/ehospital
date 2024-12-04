from django.contrib import admin
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserPermission
from .models import UserPermission, Patient, Doctor


Models = (Patient, Appointment, MedicalHistory, HealthResource,
          Facility, UserPermission, Doctor, EPrescription, Location, Department)


class UserPermissionInline(admin.StackedInline):
    model = UserPermission
    can_delete = False
    verbose_name_plural = 'permissions'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserPermissionInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Patient)
admin.site.register(Doctor)







