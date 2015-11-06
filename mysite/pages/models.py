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
    ('list_numeric', 'list_numeric'),
    ('list-checklist', 'list-checklist'),
    ('list-header', 'list-header')
)


class AbstractPlugin(CMSPlugin):
    """
    Abstract Base Class for all Plugins.
    """
    hidden = models.BooleanField(default=False)

    class Meta:
        abstract = True


class LandingPlugin(AbstractPlugin):
    """
    Plugin provide widget main page
    """
    title = models.CharField(max_length=70, null=True, blank=True)
    description = fields.HTMLField(null=True, blank=True)
    list_description = fields.HTMLField(null=True, blank=True)
    link_button = models.URLField(null=True, blank=True)
    text_button = models.CharField(null=True, max_length=70, blank=True)
    block_color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='bg-primary')


class BannerPlugin(AbstractPlugin):
    """
    Plugin make banner with description and button to go
    """
    title = models.CharField(max_length=70, blank=True)
    description = fields.HTMLField(blank=True)
    link_button = models.URLField(blank=True)
    text_button = models.CharField(max_length=70, blank=True)
    sponsors_text = models.CharField(max_length=70, blank=True)


class ActiveLearningRatesPlugin(AbstractPlugin):
    """
    Plugin provide ability to edit Active learting block.
    """
    title = models.CharField(max_length=70, blank=True)
    description = fields.HTMLField(blank=True)


class ListPlugin(AbstractPlugin):
    """
    General plugin for adding list
    of tesises with the title and <li> element class.
    """
    title = models.CharField(max_length=70, blank=True)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='list-questions')
    list_text = fields.HTMLField()


class ChildPersonalGuidesPlugin(AbstractPlugin):
    """
    Plugin for personal guides block.
    """
    image = FilerImageField(related_name="personal_guides_image")
    title = models.CharField(max_length=70, blank=True)
    description = fields.HTMLField()


class ParentPersonalGuidesPlugin(AbstractPlugin):
    """
    Parent plugin for Personal Guides.
    """
    title = models.CharField(max_length=70, blank=True)


class WorkshopDescriptionPlugin(AbstractPlugin):
    """
    Parent plugin Workshop description.
    """
    title = models.CharField(max_length=70, blank=True)


class BenefitsItemPlugin(AbstractPlugin):
    """
    Item of benefils
    """
    title = models.CharField(max_length=70, blank=True)
    description = fields.HTMLField(blank=True)
    image = FilerImageField(null=True, blank=True)


class BenefitsPlugin(AbstractPlugin):
    """
    Base plugin for benefits
    """
    title = models.CharField(max_length=70, blank=True)


class FooterPlugin(AbstractPlugin):
    """
    Plugin for the footer part of landing page.
    """
    footer_text = models.CharField(max_length=100, blank=True)
    footer_link = models.CharField(max_length=200, blank=True)


class SocialPlugin(AbstractPlugin):
    title = models.CharField(max_length=70, blank=True)


class FAQPlugin(AbstractPlugin):
    title = models.CharField(max_length=70, blank=True)


class FAQItemPlugin(AbstractPlugin):
    question = models.TextField(blank=True)
    answer = models.TextField(blank=True)


class MiscItemPlugin(AbstractPlugin):
    title = models.CharField(max_length=70, blank=True)
    description_header = fields.HTMLField(blank=True)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='list-checklist')
    list_text = fields.HTMLField()
    description_footer = fields.HTMLField(blank=True)
    header_type_text = models.CharField(max_length=70, blank=True)


class InterestedPlugin(AbstractPlugin):
    name_field = models.CharField(max_length=200, default="Name")
    email_field = models.CharField(max_length=200, default="Email")
    when_field = models.CharField(max_length=200, default="When can you join?")
    description_field = fields.HTMLField(
        default="We plan to host hackathons between ? and ?. "
                "Please tell us more about your availability below."
                "Our hackathons are split into 3 meetings that are about 2 hours long."
    )
    timezone_field = models.CharField(max_length=200, default=" What is your timezone?")


class InterestedForm(models.Model):
    """
    Model for save interested form answer and do some later
    """
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    timezone = models.CharField(max_length=70, blank=True)


class DetailsChildPlugin(AbstractPlugin):
    title = models.CharField(max_length=70, blank=True)


class DetailsVideoPlugin(AbstractPlugin):
    video_url = models.URLField()
    description = models.CharField(max_length=70)


class DetailsQuotePlugin(AbstractPlugin):
    quote_text = models.CharField(max_length=70)
    quote_small = models.CharField(max_length=70)
