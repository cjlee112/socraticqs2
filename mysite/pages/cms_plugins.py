from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.models.pluginmodel import CMSPlugin
from django.utils.translation import ugettext_lazy as _
from django.db import models
from pages.models import LandingPlugin

class LandingPagePlugin(CMSPluginBase):
    model = LandingPlugin
    render_template = "landing_page_plugin.html"


plugin_pool.register_plugin(LandingPagePlugin)
