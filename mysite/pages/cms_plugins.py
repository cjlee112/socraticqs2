import re

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

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
    DetailsPlugin,
    MiscItemPlugin
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
    require_parent = True
    child_classes = ['ChildPersonalGuidesPagePlugin']
    parent_classes = ['WorkshopDescriptionPagePlugin']


class WorkshopDescriptionPagePlugin(CMSPluginBase):
    render_template = 'pages/workshop_description_plugin.html'
    name = 'Workshop Description Base Plugin'
    model = WorkshopDescriptionPlugin
    allow_children = True
    child_classes = ['ParentPersonalGuidesPagePlugin', 'MiscDetailContainer']


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
    parent_classes = ['FAQPagePlugin', 'DetailsPagePlugin']


class FAQPagePlugin(CMSPluginBase):
    model = FAQPlugin
    render_template = 'pages/faq_plugin.html'
    allow_children = True
    child_classes = ['FAQItemPagePlugin']


class DetailsPagePlugin(CMSPluginBase):
    model = DetailsPlugin
    render_template = 'pages/details_child_plugin.html'
    allow_children = True
    child_classes = ['FAQItemPagePlugin']
    require_parent = True
    parent_classes = ['MiscDetailContainer']


class MiscPagePlugin(CMSPluginBase):
    render_template = 'pages/misc_plugin.html'
    allow_children = True
    child_classes = ['MiscItemPagePlugin']
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
    child_classes = ['DetailsPagePlugin', 'MiscPagePlugin']
    require_parent = True
    parent_classes = ['WorkshopDescriptionPagePlugin']


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
