from django.db import models
from djangocms_text_ckeditor import fields
from cms.models.pluginmodel import CMSPlugin
from filer.fields.image import FilerImageField


COLOR_CHOICES = (
    ("bg-primary", "blue"),
    ("bg-danger", "red"),
    ("bg-success", "green"),
    ("bg-info", "light-blue"),
    ("bg-warning", "yellow"),

)


class LandingPlugin(CMSPlugin):
    """
    Plugin provide widget landing page
    """
    title = models.CharField(max_length=70, null=True, blank=True)
    description = fields.HTMLField(null=True, blank=True)
    list_description = fields.HTMLField(null=True, blank=True)
    link_button = models.URLField(null=True, blank=True)
    text_button = models.CharField(null=True, max_length=70, blank=True)
    block_color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='bg-primary')


class BannerPlugin(CMSPlugin):
    """
    Plugin make banner with description and button to go
    """
    title = models.CharField(max_length=70, blank=True)
    description = fields.HTMLField(blank=True)
    link_button = models.URLField(blank=True)
    text_button = models.CharField(max_length=70, blank=True)
    background_image = FilerImageField(null=True, blank=True)
