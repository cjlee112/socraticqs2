import re
from django.db import models
from collections import OrderedDict
from django.core.urlresolvers import reverse, NoReverseMatch
from django.conf import settings

from ct.models import Course, CourseUnit, Unit, UnitLesson, Lesson, Response
from ctms.urls import urlpatterns as ctms_urls
from .views import CourseCoursletUnitMixin

# course, courslet, unit
MODEL_ORDER_TUPLE = (('course_pk', Course), ('courslet_pk', CourseUnit), ('unit_pk', UnitLesson), ('response_pk', Response))
MODELS_ORDERED_DICT = OrderedDict(MODEL_ORDER_TUPLE)

MODEL_NAMES_MAPPING = {
    Course: 'course',
    CourseUnit: 'courslet',
    UnitLesson: 'unit',
    Response: 'response'
}

NAME_MODEL_MAPPING = {
    'Course': Course,
    'Response': Response,
    'Unit': UnitLesson,
    'CourseUnit': CourseUnit
}


class SideBarUtils(object):
    '''
    Utils class.
    '''
    def __init__(self):
        # before using this mixin we have to attach request to mixin's instance
        self.course_mixin = CourseCoursletUnitMixin()

    def _get_model_ids(self, kwargs):
        '''
        :param kwargs:
        :return:
        '''
        model_ids = dict()
        last_pk = None
        _, default_model = MODELS_ORDERED_DICT.items()[0]
        for kw, model in MODELS_ORDERED_DICT.items():
            if kw in kwargs:
                last_pk = kw
                model_ids[MODELS_ORDERED_DICT[kw]] = kwargs[kw]
        if 'pk' in kwargs:
            if last_pk is None:
                model_ids[default_model] = kwargs['pk']
            else:
                model_ids[
                    MODELS_ORDERED_DICT.items()[MODELS_ORDERED_DICT.keys().index(last_pk) + 1][1]
                ] = kwargs['pk']
        return model_ids

    def _get_objects(self, model_ids):
        '''
        Yields pairs of name, object.
        Name is translated according with mapping.
        :param model_ids: dict returned from _get_model_ids
        :return:
        '''
        for model, pk in model_ids.items():
            yield (MODEL_NAMES_MAPPING[model], model.objects.filter(id=pk).first())

    def _reverse(self, name, kwargs=None):
        namespace = getattr(settings, 'CTMS_URL_NAMESPACE', 'ctms')
        return reverse('{}:{}'.format(namespace, name), kwargs=kwargs)

    def _get_url_kwargs(self, url):
        kwarg_re = r'\(\?\P\<(\w+)>+?'
        kwargs = re.findall(kwarg_re, url.regex.pattern)
        return kwargs

    def _get_urls(self, request):
        """
        retur: dict with urls like
        {
        'course_urls':{
            '1':{
                'url.name': '/some/url'
                }
            }
        'courslet_urls':
            '1':{
                'url.name': '/some/url'
                }
            }
        'unit_urls':
            '1':{
                'url.name': '/some/url'
                }
            }
        'response_urls':
            '1':{
                'url.name': '/some/url'
                }
            }
        }
        """
        all_urls = {}
        def add_url(to, url_name, obj_id, url):
            all_urls.setdefault(
                to, {}
            ).setdefault(
                obj_id, {}
            )[url_name] = url

        def parse_url_name(url_name):
            instances = ('course', 'courslet', 'unit',
                         'response', 'shared')
            instance, action = url_name.split('_', 1)
            if instance not in instances:
                for inst in instances:
                    if inst in url_name:
                        action = url_name.replace(inst, '').replace('_', '')
                        instance = inst
            return instance, action

        for url in ctms_urls:
            url_kw = self._get_url_kwargs(url)
            try:
                kwargs = self._translate_kwargs(request, url_kw)
                _url = self._reverse(url.name, kwargs)
                # course_pk = kwargs.get('course_pk')
                # courslet_pk = kwargs.get('courslet_pk')
                if 'course' in url.name:
                    pk = kwargs.get('pk')
                    add_url('course_urls', url.name, pk, _url)
                elif 'courslet' in url.name:
                    pk = kwargs.get('pk')
                    add_url('courslet_urls', url.name, pk, _url)
                elif 'unit' in url.name:
                    pk = kwargs.get('pk')
                    add_url('unit_urls', url.name, pk, _url)
                elif 'response' in url.name:
                    pk = kwargs.get('pk')
                    add_url('unit_urls', url.name, pk, _url)
                all_urls.setdefault('all_urls', {})[url.name] = _url
            except NoReverseMatch:
                continue
        return all_urls

    def _get_model_from_request(self, request, name):
        return getattr(getattr(request, MODEL_NAMES_MAPPING[name], None), 'id', None)

    def _translate_kwargs(self, request, kwargs_list):
        last_pk = None
        _, default_model = MODELS_ORDERED_DICT.items()[0]
        result_kwargs = {}

        for kw, model in MODELS_ORDERED_DICT.items():
            if kw in kwargs_list:
                result_kwargs[kw] = self._get_model_from_request(request, model)
                last_pk = kw
        if 'pk' in kwargs_list:
            if last_pk is None:
                result_kwargs['pk'] = self._get_model_from_request(request, default_model)
            else:
                next_model = MODELS_ORDERED_DICT.items()[MODELS_ORDERED_DICT.keys().index(last_pk) + 1]
                result_kwargs['pk'] = self._get_model_from_request(request, next_model[1])
        return result_kwargs


class SideBarMiddleware(SideBarUtils):
    def process_view(self, request, view_func, view_args, view_kwargs):
        urls = self._get_urls(request)
        if 'ctms' in request.path and request.path != urls['all_urls']['my_courses']:
            model_ids = self._get_model_ids(view_kwargs)
            objects = self._get_objects(model_ids)
            # attach recieved objects to request object
            for name, obj in objects:
                setattr(request, name, obj)

            # attach object id's to session
            obj_ids = {}
            for cls, o_id in model_ids.items():
                obj_ids[cls.__name__] = o_id
            request.session['sidebar_object_ids'] = obj_ids
        return None

    def process_template_response(self, request, response):
        # add request to mixin
        self.course_mixin.request = request
        sidebar_context = {}
        my_courses = self.course_mixin.get_my_courses() if request.user.is_authenticated() else Course.objects.none()
        sidebar_context['user_courses'] = my_courses
        if 'ctms' in request.path and not request.session.get('sidebar_object_ids', {}):
            for model, name in MODEL_NAMES_MAPPING.items():
                sidebar_context[name] = getattr(request, name, None)
            # urls = self._get_urls(request)
            # sidebar_context['urls'] = urls
        elif request.session.get('sidebar_object_ids'):
            objects = dict(self._get_objects({
                model: request.session.get('sidebar_object_ids', {}).get(name)
                for name, model in NAME_MODEL_MAPPING.items()
            }))
            sidebar_context.update(objects)

        if sidebar_context.get('course'):
            courslets = self.course_mixin.get_courselets_by_course(sidebar_context['course'])
            sidebar_context['course_courslets'] = courslets

        if sidebar_context.get('courslet'):
            sidebar_context['courslet_units'] = self.course_mixin.get_units_by_courselet(
                sidebar_context['courslet']
            )

        if response.context_data:
            response.context_data['sidebar'] = sidebar_context
            response.render()

        return response
