from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from pages.models import (
    LandingPlugin,
    ShortAboutPlugin,
    BannerPlugin,
    ActiveLearningRatesPlugin
)


class LandingPagePlugin(CMSPluginBase):
    model = LandingPlugin
    render_template = "pages/landing_page_plugin.html"


class BannerPlugin(CMSPluginBase):
    model = BannerPlugin
    render_template = "pages/banner_plugin.html"


class ShortAboutPagePlugin(CMSPluginBase):
    model = ShortAboutPlugin
    render_template = 'pages/short_about_plugin.html'


class ActiveLearningRatesPagePlugin(CMSPluginBase):
    model = ActiveLearningRatesPlugin
    render_template = 'pages/active_learning_rates_plugin.html'


plugin_pool.register_plugin(BannerPlugin)
plugin_pool.register_plugin(LandingPagePlugin)
plugin_pool.register_plugin(ShortAboutPagePlugin)
plugin_pool.register_plugin(ActiveLearningRatesPagePlugin)
