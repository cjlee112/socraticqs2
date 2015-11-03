from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.models.pluginmodel import CMSPlugin
from django.utils.translation import ugettext_lazy as _
from django.db import models
from models import LandingPlugin, BannerPlugin

class LandingPagePlugin(CMSPluginBase):
    model = LandingPlugin
    render_template = "pages/landing_page_plugin.html"


class BannerPlugin(CMSPluginBase):
    model = BannerPlugin
    render_template = "pages/banner_plugin.html"

plugin_pool.register_plugin(LandingPagePlugin)
plugin_pool.register_plugin(BannerPlugin)
