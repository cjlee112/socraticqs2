from django.contrib import admin

from psa.models import UserSession, AnonymEmail


admin.site.register(UserSession)
admin.site.register(AnonymEmail)
