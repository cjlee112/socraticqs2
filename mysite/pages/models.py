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


LIST_TYPES = (
    ('list-questions', 'list-questions'),
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
    sponsors_text = models.CharField(max_length=70, blank=True)


class ActiveLearningRatesPlugin(CMSPlugin):
    """
    Plugin provide ability to edit Active learting block.
    """
    title = models.CharField(max_length=70, blank=True)
    description = fields.HTMLField(blank=True)


class ListPlugin(CMSPlugin):
    """
    General plugin for adding list
    of tesises with the title and <li> element class.
    """
    title = models.CharField(max_length=70, blank=True)
    description_header = fields.HTMLField(blank=True)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='list-questions')
    list_text = fields.HTMLField()
    description_footer = fields.HTMLField(blank=True)


class ChildPersonalGuidesPlugin(CMSPlugin):
    """
    Plugin for personal guides block.
    """
    image = FilerImageField(related_name="personal_guides_image")
    title = models.CharField(max_length=70, blank=True)
    description = fields.HTMLField()


class ParentPersonalGuidesPlugin(CMSPlugin):
    """
    Parent plugin for Personal Guides.
    """
    title = models.CharField(max_length=70, blank=True)


class WorkshopDescriptionPlugin(CMSPlugin):
    """
    Parent plugin Workshop description.
    """
    title = models.CharField(max_length=70, blank=True)


class BenefitsItemPlugin(CMSPlugin):
    """
    Item of benefils
    """
    title = models.CharField(max_length=70, blank=True)
    description = fields.HTMLField(blank=True)
    image = FilerImageField(null=True, blank=True)


class BenefitsPlugin(CMSPlugin):
    """
    Base plugin for benefits
    """
    title = models.CharField(max_length=70, blank=True)


class FooterPlugin(CMSPlugin):
    """
    Plugin for the footer part of landing page.
    """
    footer_text = models.CharField(max_length=100, blank=True)
    footer_link = models.CharField(max_length=200, blank=True)


class SocialPlugin(CMSPlugin):
    title = models.CharField(max_length=70, blank=True)


class FAQPlugin(CMSPlugin):
    title = models.CharField(max_length=70, blank=True)


class FAQItemPlugin(CMSPlugin):
    question = models.TextField(blank=True)
    answer = models.TextField(blank=True)


class DetailsPlugin(CMSPlugin):
    title = models.CharField(max_length=70, blank=True)
    video_url = models.URLField()
    details_text = models.CharField(max_length=70)
    quote_text = models.CharField(max_length=70)
    quote_small = models.CharField(max_length=70)
