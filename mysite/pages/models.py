# -*- coding: utf-8 -*-
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

SLIDE_SHARE_BACK = (
    ('gray', 'section-2-cols-bg'),
    ('none', ''),
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
    title = models.CharField(max_length=200, null=True, blank=True)
    description = fields.HTMLField(null=True, blank=True)
    list_description = fields.HTMLField(null=True, blank=True)
    link_button = models.URLField(null=True, blank=True)
    text_button = models.CharField(null=True, max_length=70, blank=True)
    block_color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='bg-primary')


class BannerPlugin(AbstractPlugin):
    """
    Plugin make banner with description and button to go
    """
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField(blank=True)
    link_button = models.URLField(blank=True)
    text_button = models.CharField(max_length=70, blank=True)
    sponsors_text = models.CharField(max_length=200, blank=True)


class ActiveLearningRatesPlugin(AbstractPlugin):
    """
    Plugin provide ability to edit Active learting block.
    """
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField(blank=True)
    fig_alt = models.CharField(max_length=200, blank=True)
    fig_caption = models.CharField(max_length=200, blank=True)
    list_text = fields.HTMLField()


class ListPlugin(AbstractPlugin):
    """
    General plugin for adding list
    of tesises with the title and <li> element class.
    """
    title = models.CharField(max_length=200, blank=True)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='list-questions')
    list_text = fields.HTMLField()


class ChildPersonalGuidesPlugin(AbstractPlugin):
    """
    Plugin for personal guides block.
    """
    image = FilerImageField(related_name="personal_guides_image")
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField()


class SocialProofsPlugin(AbstractPlugin):
    """
    Plugin for Social Proofs block.
    """
    title = models.CharField(max_length=200, blank=True)
    post_description = fields.HTMLField()
    more_proofs_link = models.URLField(null=True, blank=True)


class ProofPlugin(AbstractPlugin):
    """
    Plugin for proof.
    """
    proof_icon = FilerImageField(related_name="proof_icon", blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField()


class KeyNotesSetPlugin(AbstractPlugin):
    """
    Plugin for KeyNotes block.
    """
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField()


class KeyNotePlugin(AbstractPlugin):
    """
    Plugin for KeyNote.
    """
    button_text = models.CharField(max_length=200, blank=True)
    uid = models.SlugField(max_length=8, blank=False)
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField()


class ParentPersonalGuidesPlugin(AbstractPlugin):
    """
    Parent plugin for Personal Guides.
    """
    title = models.CharField(max_length=200, blank=True)


class WorkshopDescriptionPlugin(AbstractPlugin):
    """
    Parent plugin Workshop description.
    """
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField(blank=True)


class BenefitsItemPlugin(AbstractPlugin):
    """
    Item of benefils
    """
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField(blank=True)
    image = FilerImageField(null=True, blank=True)


class BenefitsPlugin(AbstractPlugin):
    """
    Base plugin for benefits
    """
    title = models.CharField(max_length=200, blank=True)
    description = fields.HTMLField(blank=True)


class FooterPlugin(AbstractPlugin):
    """
    Plugin for the footer part of landing page.
    """
    footer_text = models.CharField(max_length=100, blank=True)
    footer_link = models.CharField(max_length=200, blank=True)


class SocialPlugin(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)


class FAQPlugin(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)


class FAQItemPlugin(AbstractPlugin):
    question = models.TextField(blank=True)
    answer = models.TextField(blank=True)


class MiscItemPlugin(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)
    description_header = fields.HTMLField(blank=True)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='list-checklist')
    list_text = fields.HTMLField()
    description_footer = fields.HTMLField(blank=True)
    header_type_text = models.CharField(max_length=200, blank=True)


class InterestedPlugin(AbstractPlugin):
    title = models.CharField(max_length=200, default="I’m Interested in the hackathon")
    description = models.TextField(
        default="Get on our mailing list and we’ll contact you about the next hackathon.")
    name_field = models.CharField(max_length=200, default="Name")
    email_field = models.CharField(max_length=200, default="Email")
    organization_field = models.CharField(max_length=200, default="Institution/Organization")

    role_field = models.CharField(max_length=200, default=" Title/Role")

    name_error_msg = models.CharField(max_length=200, default="Please enter your name")
    organization_error_msg = models.CharField(max_length=200, default="Please enter your Institute/Organization")
    email_error_msg = models.CharField(max_length=200, default="Please enter your email")
    role_error_msg = models.CharField(max_length=200, default="Please enter your Title/Role")

    email_to = models.EmailField(default='dummy@mail.com')

    btn_text = models.CharField(max_length=70, default='Schedule to demo')
    bg_image = FilerImageField(null=True, blank=True)


class InterestedForm(models.Model):
    """
    Model for save interested form answer and do some later
    """
    name = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)


class DetailsChildPlugin(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)


class DetailsVideoPlugin(AbstractPlugin):
    video_url = models.URLField()
    description = models.CharField(max_length=200, blank=True)


class DetailsQuotePlugin(AbstractPlugin):
    quote_text = models.CharField(max_length=200)
    quote_small = models.CharField(max_length=200)


class SlideSharePlugin(AbstractPlugin):
    title = models.CharField(max_length=200)
    description = fields.HTMLField()
    background = models.CharField(default='grey', max_length=70, choices=SLIDE_SHARE_BACK)


class SlideShareItemPlugin(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)
    slideshare_code = models.TextField()


class BecomeInstructorPlugin(AbstractPlugin):
    error_name = models.CharField(max_length=200, blank=True)
    agreement_text = models.TextField(blank=True)


class HelpCenterModel(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    link_text = models.CharField(max_length=200)
    link_url = models.URLField()


class IntercomArticleModel(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)
    short_description = models.TextField(blank=True)
    link_text = models.CharField(max_length=200)
    link_url = models.URLField()


class Hero1Model(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    best_prattices_text = models.CharField(max_length=200)
    best_prattices_link = models.URLField()
    bp1_text = models.CharField(max_length=200)
    bp1_link = models.URLField()
    video_url = models.URLField()


class Hero2Model(AbstractPlugin):
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    best_prattices_text = models.CharField(max_length=200)
    best_prattices_link = models.URLField()
    bp2_text = models.CharField(max_length=200)
    bp2_link = models.URLField()
    video_url = models.URLField()
