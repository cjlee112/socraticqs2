from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from pages.models import (
    LandingPlugin,
    ShortAboutPlugin,
    BannerPlugin,
    ActiveLearningRatesPlugin,
    ListPlugin
)


class LandingPagePlugin(CMSPluginBase):
    model = LandingPlugin
    render_template = "pages/landing_plugin.html"


class BannerPagePlugin(CMSPluginBase):
    model = BannerPlugin
    render_template = "pages/banner_plugin.html"


class ShortAboutPagePlugin(CMSPluginBase):
    model = ShortAboutPlugin
    render_template = 'pages/short_about_plugin.html'


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
            'list_text': instance.list_text.split(),
        })
        return context


plugin_pool.register_plugin(BannerPagePlugin)
plugin_pool.register_plugin(LandingPagePlugin)
plugin_pool.register_plugin(ShortAboutPagePlugin)
plugin_pool.register_plugin(ActiveLearningRatesPagePlugin)
plugin_pool.register_plugin(ListPagePlugin)
