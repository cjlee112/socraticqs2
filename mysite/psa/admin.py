from django.contrib import admin
from psa.custom_django_storage import CustomCode

from psa.models import UserSession, AnonymEmail, SecondaryEmail


@admin.register(SecondaryEmail)
class SecondaryEmailAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'provider')

@admin.register(CustomCode)
class CustomCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'user_id', 'verified')

admin.site.register(UserSession)
admin.site.register(AnonymEmail)
