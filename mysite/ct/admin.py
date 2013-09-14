from django.contrib import admin
import ct.models

admin.site.register(ct.models.Question)
admin.site.register(ct.models.ErrorModel)
admin.site.register(ct.models.Response)
admin.site.register(ct.models.StudentError)
admin.site.register(ct.models.Remediation)
admin.site.register(ct.models.Glossary)
admin.site.register(ct.models.Vocabulary)
admin.site.register(ct.models.ConceptPicture)
admin.site.register(ct.models.ConceptEquation)
