from django.conf.urls import patterns, include, url
from ct.views import *

urlpatterns = patterns('',
    (r'^$', main_page),
    url(r'^(?P<ct_id>\d+)/responses/$', respond, name='respond'),
    url(r'^unitq/(?P<unitq_id>\d+)/responses/$', respond_unitq, name='respond_unitq'),
    url(r'^resp/(?P<resp_id>\d+)/assess/$', assess_page, name='assess'),
    url(r'^resp/(?P<resp_id>\d+)/evaluate/$', submit_eval, name='evaluate'),
    url(r'^err/(?P<em_id>\d+)/remedy/$', remedy_page, name='remedy'),
    url(r'^err/(?P<em_id>\d+)/remediate/$', submit_remedy, name='remediate'),
    url(r'^gloss/(?P<glossary_id>\d+)/write/$', glossary_page, name='write_glossary'),
    url(r'^gloss/(?P<glossary_id>\d+)/new_term/$', submit_term, name='new_term'),

)

