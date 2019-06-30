import re

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from pages.forms import BecomeInstructorForm
from pages.models import (
    LandingPlugin,
    BannerPlugin,
    ActiveLearningRatesPlugin,
    ListPlugin,
    ChildPersonalGuidesPlugin,
    ParentPersonalGuidesPlugin,
    WorkshopDescriptionPlugin,
    BenefitsPlugin,
    BenefitsItemPlugin,
    FooterPlugin,
    SocialPlugin,
    FAQPlugin,
    FAQItemPlugin,
    MiscItemPlugin,
    InterestedPlugin,
    DetailsChildPlugin,
    DetailsVideoPlugin,
    DetailsQuotePlugin,
    SlideShareItemPlugin,
    SlideSharePlugin,
    SocialProofsPlugin,
    ProofPlugin,
    KeyNotesSetPlugin,
    KeyNotePlugin,
    HelpCenterModel,
    IntercomArticleModel,
    Hero1Model,
    Hero2Model,
    BecomeInstructorPlugin as BecomeInstructorPluginModel,
)


class LandingPagePlugin(CMSPluginBase):
    model = LandingPlugin
    render_template = "pages/landing_plugin.html"


class BannerPagePlugin(CMSPluginBase):
    model = BannerPlugin
    render_template = "pages/banner_plugin.html"


class ActiveLearningRatesPagePlugin(CMSPluginBase):
    model = ActiveLearningRatesPlugin
    render_template = 'pages/active_learning_rates_plugin.html'

    def render(self, context, instance, placeholder):
        context.update({
            'instance': instance,
            'placeholder': placeholder,
            'list_text': re.findall(r'<li>.+</li>', instance.list_text),
        })
        return context


class ListPagePlugin(CMSPluginBase):
    model = ListPlugin
    render_template = 'pages/list_plugin.html'

    def render(self, context, instance, placeholder):
        context.update({
            'instance': instance,
            'placeholder': placeholder,
            'list_text': re.findall(r'<li>.+</li>', instance.list_text),
        })
        return context


class ChildPersonalGuidesPagePlugin(CMSPluginBase):
    render_template = 'pages/personal_guides_child.html'
    name = 'Personal_Guides_Child'
    model = ChildPersonalGuidesPlugin
    require_parent = True
    parent_classes = ['ParentPersonalGuidesPagePlugin']


class ParentPersonalGuidesPagePlugin(CMSPluginBase):
    render_template = 'pages/personal_guides_parent.html'
    name = 'Personal_Guides_Parent'
    model = ParentPersonalGuidesPlugin
    allow_children = True
    child_classes = ['ChildPersonalGuidesPagePlugin']


class WorkshopDescriptionPagePlugin(CMSPluginBase):
    render_template = 'pages/workshop_description_plugin.html'
    name = 'Workshop Description Base Plugin'
    model = WorkshopDescriptionPlugin
    allow_children = True
    child_classes = ['MiscDetailContainer']


class BenefitsItemPagePlugin(CMSPluginBase):
    model = BenefitsItemPlugin
    render_template = 'pages/benefits_item_plugin.html'
    require_parent = True
    parent_classes = ['BenefitPagePlugin']


class BenefitPagePlugin(CMSPluginBase):
    model = BenefitsPlugin
    render_template = 'pages/benefits_plugin.html'
    allow_children = True
    child_classes = ['BenefitsItemPagePlugin']


class FooterPagePlugin(CMSPluginBase):
    render_template = 'pages/landing_footer_plugin.html'
    name = 'Landing Page Footer Plugin'
    model = FooterPlugin


class LandingPageSocialPlugin(CMSPluginBase):
    render_template = 'pages/landing_social_plugin.html'
    name = 'Landing Page Social Plugin'
    model = SocialPlugin


class FAQItemPagePlugin(CMSPluginBase):
    model = FAQItemPlugin
    render_template = 'pages/faq_item_plugin.html'
    require_parent = True
    parent_classes = ['FAQPagePlugin', 'DetailsChildPagePlugin']


class FAQPagePlugin(CMSPluginBase):
    model = FAQPlugin
    render_template = 'pages/faq_plugin.html'
    allow_children = True
    child_classes = ['FAQItemPagePlugin']


class DetailsPagePlugin(CMSPluginBase):
    render_template = 'pages/details_contaiter_plugin.html'
    allow_children = True
    child_classes = ['DetailsChildPagePlugin', 'DetailsVideoPagePlugin', 'DetailsQuotePagePlugin']
    require_parent = True
    parent_classes = ['MiscDetailContainer']


class MiscPagePlugin(CMSPluginBase):
    render_template = 'pages/misc_plugin.html'
    allow_children = True
    require_parent = True
    parent_classes = ['MiscDetailContainer']


class MiscItemPagePlugin(CMSPluginBase):
    model = MiscItemPlugin
    render_template = 'pages/misc_item_plugin.html'
    require_parent = True
    parent_classes = ['MiscPagePlugin']

    def render(self, context, instance, placeholder):
        context.update({
            'instance': instance,
            'placeholder': placeholder,
            'list_text': re.findall(r'<li>.+</li>', instance.list_text),
        })
        return context


class MiscDetailContainer(CMSPluginBase):
    render_template = 'pages/misc_detail_container_plugin.html'
    allow_children = True
    child_classes = ['ListPagePlugin', 'SlideShareItemPagePlugin']
    require_parent = True
    parent_classes = ['WorkshopDescriptionPagePlugin']


class InterestedPagePlugin(CMSPluginBase):
    model = InterestedPlugin
    render_template = 'pages/interested_plugin.html'
    cache = False


class DetailsChildPagePlugin(CMSPluginBase):
    model = DetailsChildPlugin
    render_template = 'pages/details_child_plugin.html'
    allow_children = True
    child_classes = ['FAQItemPagePlugin']
    require_parent = True
    parent_classes = ['DetailsPagePlugin']


class DetailsVideoPagePlugin(CMSPluginBase):
    model = DetailsVideoPlugin
    render_template = 'pages/details_video_plugin.html'
    require_parent = True
    parent_classes = ['DetailsPagePlugin', 'SlideSharePagePlugin', 'InlineSlideSharePagePlugin']


class DetailsQuotePagePlugin(CMSPluginBase):
    model = DetailsQuotePlugin
    render_template = 'pages/details_quote_plugin.html'
    require_parent = True
    parent_classes = ['DetailsPagePlugin']


class SlideShareItemPagePlugin(CMSPluginBase):
    model = SlideShareItemPlugin
    render_template = 'pages/slideshareitem_plugin.html'
    require_parent = True
    parent_classes = ['SlideSharePagePlugin', 'MiscDetailContainer']


class SlideSharePagePlugin(CMSPluginBase):
    """docstring for SlideSharePagePlugin"""
    model = SlideSharePlugin
    render_template = 'pages/slideshare_plugin.html'
    allow_children = True
    child_classes = ['SlideShareItemPagePlugin', 'DetailsVideoPagePlugin']


class InlineSlideSharePagePlugin(CMSPluginBase):
    """docstring for SlideSharePagePlugin"""
    model = SlideSharePlugin
    render_template = 'pages/inline_slideshare_plugin.html'
    allow_children = True
    child_classes = ['SlideShareItemPagePlugin', 'DetailsVideoPagePlugin']


class SplitTwoColumns(CMSPluginBase):
    render_template = 'pages/split_two_cols.html'
    allow_children = True


class SocialProofs(CMSPluginBase):
    model = SocialProofsPlugin
    render_template = 'pages/social_proofs.html'
    allow_children = True
    child_classes = ['ProofColumn']


class ProofColumn(CMSPluginBase):
    render_template = 'pages/proof_column.html'
    allow_children = True
    child_classes = ['Proof']


class Proof(CMSPluginBase):
    model = ProofPlugin
    render_template = 'pages/proof.html'
    allow_children = False


class KeyNotesSet(CMSPluginBase):
    model = KeyNotesSetPlugin
    render_template = 'pages/keynotes_set.html'
    allow_children = True
    child_classes = ['KeyNote']


class KeyNote(CMSPluginBase):
    model = KeyNotePlugin
    render_template = 'pages/keynote.html'
    allow_children = False


class SplitThreeColumns(CMSPluginBase):
    render_template = 'pages/split_three_cols.html'
    allow_children = True


class BecomeInstructorPlugin(CMSPluginBase):
    render_template = 'pages/become_instructor_plugin.html'
    model = BecomeInstructorPluginModel

    def render(self, context, instance, placeholder):
        context.update({
            'instance': instance,
            'placeholder': placeholder,
            'form': BecomeInstructorForm(),
        })
        return context


class HelpCenterPlugin(CMSPluginBase):
    model = HelpCenterModel
    render_template = 'pages/help_center_plugin.html'
    allow_children = True


class IntercomArticlePlugin(CMSPluginBase):
    model = IntercomArticleModel
    render_template = 'pages/intercom_article_plugin.html'
    allow_children = False


class Hero1Plugin(CMSPluginBase):
    model = Hero1Model
    render_template = 'pages/hero1_plugin.html'
    allow_children = True


class Hero2Plugin(CMSPluginBase):
    model = Hero2Model
    render_template = 'pages/hero2_plugin.html'
    allow_children = True


plugin_pool.register_plugin(BecomeInstructorPlugin)
plugin_pool.register_plugin(BannerPagePlugin)
plugin_pool.register_plugin(LandingPagePlugin)
plugin_pool.register_plugin(ActiveLearningRatesPagePlugin)
plugin_pool.register_plugin(ListPagePlugin)
plugin_pool.register_plugin(ParentPersonalGuidesPagePlugin)
plugin_pool.register_plugin(ChildPersonalGuidesPagePlugin)
plugin_pool.register_plugin(WorkshopDescriptionPagePlugin)
plugin_pool.register_plugin(BenefitPagePlugin)
plugin_pool.register_plugin(BenefitsItemPagePlugin)
plugin_pool.register_plugin(FooterPagePlugin)
plugin_pool.register_plugin(LandingPageSocialPlugin)
plugin_pool.register_plugin(FAQItemPagePlugin)
plugin_pool.register_plugin(FAQPagePlugin)
plugin_pool.register_plugin(DetailsPagePlugin)
plugin_pool.register_plugin(MiscPagePlugin)
plugin_pool.register_plugin(MiscItemPagePlugin)
plugin_pool.register_plugin(MiscDetailContainer)
plugin_pool.register_plugin(InterestedPagePlugin)
plugin_pool.register_plugin(DetailsChildPagePlugin)
plugin_pool.register_plugin(DetailsVideoPagePlugin)
plugin_pool.register_plugin(DetailsQuotePagePlugin)
plugin_pool.register_plugin(SlideShareItemPagePlugin)
plugin_pool.register_plugin(SlideSharePagePlugin)
plugin_pool.register_plugin(InlineSlideSharePagePlugin)
plugin_pool.register_plugin(SplitTwoColumns)
plugin_pool.register_plugin(SplitThreeColumns)
plugin_pool.register_plugin(SocialProofs)
plugin_pool.register_plugin(ProofColumn)
plugin_pool.register_plugin(Proof)
plugin_pool.register_plugin(KeyNotesSet)
plugin_pool.register_plugin(KeyNote)
plugin_pool.register_plugin(HelpCenterPlugin)
plugin_pool.register_plugin(IntercomArticlePlugin)
plugin_pool.register_plugin(Hero1Plugin)
plugin_pool.register_plugin(Hero2Plugin)
