from django.conf.urls import patterns, include, url
from ct.views import *

urlpatterns = patterns('',
    (r'^$', main_page),
    url(r'^(?P<ct_id>\d+)/$', question, name='question'),
    url(r'^unit/(?P<unit_id>\d+)/$', unit, name='unit'),
    url(r'^(?P<ct_id>\d+)/studylist/$', flag_question, name='flag_question'),
    url(r'^(?P<ct_id>\d+)/respond/$', respond, name='respond'),
    url(r'^unitq/$', new_unitq, name='unitq'),
    url(r'^unitq/(?P<unitq_id>\d+)/respond/$', respond_unitq, name='respond_unitq'),
    url(r'^unitq/(?P<unitq_id>\d+)/start/$', unitq_live_start, name='livestart'),
    url(r'^unitq/(?P<unitq_id>\d+)/control/$', unitq_control, name='control'),
    url(r'^unitq/(?P<unitq_id>\d+)/end/$', unitq_end, name='end'),
    url(r'^unitq/(?P<unitq_id>\d+)/wait/$', wait, name='wait'),
    url(r'^resp/(?P<resp_id>\d+)/assess/$', assess, name='assess'),
    url(r'^err/(?P<em_id>\d+)/remedy/$', remedy_page, name='remedy'),
    url(r'^err/(?P<em_id>\d+)/remediate/$', submit_remedy, name='remediate'),
    url(r'^gloss/(?P<glossary_id>\d+)/write/$', glossary_page, name='write_glossary'),
    url(r'^gloss/(?P<glossary_id>\d+)/new_term/$', submit_term, name='new_term'),

)

