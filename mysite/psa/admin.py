from django.contrib import admin

from psa.models import UserSession, AnonymEmail, SecondaryEmail


@admin.register(SecondaryEmail)
class SecondaryEmailAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'provider')


admin.site.register(UserSession)
admin.site.register(AnonymEmail)
