import time
import logging
import datetime

from rest_framework import viewsets, status, generics, exceptions, pagination
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response as RestResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models import Q, F, Max, Count
from django.db.models.functions import Length
from django.contrib.auth.models import User

from accounts.models import Instructor, create_unique_user
from analytics.models import CourseReport
from analytics.tasks import report
from ct.models import CourseUnit, Response, StudentError, Course, Role, Unit, UnitLesson, Lesson, ExternalContentHash
from chat.models import Chat, EnrollUnitCode
from ctms.models import BestPractice, BestPracticeTemplate, Invite, InviteReplayError
from core.common.mongo import do_health, c_onboarding_status
from core.common import onboarding
from core.common.utils import get_onboarding_steps, get_onboarding_status_with_settings, create_onboarding_event, make_random_password
from ..permissions import IsInstructor
from ..serializers import (
    ResponseSerializer,
    ErrorSerializer,
    CourseReportSerializer,
    UnitSerializer,
    ThreadSerializer,
    UnitSerializer2,
    ORCTSerializer3,
    ULSerializer3,
    get_ul_serializer,
    ResponseSerializer2,
    StudentErrorSerializer,
    TrivialSerializer,
    ECHSerializer,
    Text2HtmlULSerializer,
)
from .utils import get_result_course_calculation, get_result_courselet_calculation
from .creators import ThreadBuilder


logger = logging.getLogger(__name__)


class ResponseViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Django RestFramework class to implement Course student responses report.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = Response.objects.filter(kind='orct', unitLesson__order__isnull=False)
    serializer_class = ResponseSerializer

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        self.check_object_permissions(
            self.request, course
        )
        queryset = super(ResponseViewSet, self).get_queryset()
        return queryset.filter(course__id=self.kwargs.get('course_id'))


class ErrorViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Django RestFramework class to implement Course student errors report.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = StudentError.objects.all()
    serializer_class = ErrorSerializer

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        self.check_object_permissions(
            self.request, course
        )
        queryset = super(ErrorViewSet, self).get_queryset()
        return queryset.filter(response__course__id=self.kwargs.get('course_id'))


class GenReportView(APIView):
    """
    Start `report` Celery task for `course_id`.
    """
    authentication_classes = (SessionAuthentication,)

    def get(self, request, format=None):
        course_id = request.GET.get('course_id')
        if not course_id:
            return RestResponse('course_id is not provided', status=400)
        course = get_object_or_404(Course, id=course_id)
        course_instructors = course.role_set.filter(role=Role.INSTRUCTOR).values_list('user_id', flat=True)
        if (
                request.user.id not in course_instructors and
                not course.addedBy == request.user
        ):
            return RestResponse('action is not allowed', status=403)
        report.delay(course_id, request.user.id)
        return RestResponse(status=200)


class CourseReportViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Returns CourseReports for current Course.
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = CourseReport.objects.all()
    serializer_class = CourseReportSerializer

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        self.check_object_permissions(
            self.request, course
        )
        queryset = super(CourseReportViewSet, self).get_queryset()
        return queryset.filter(course=course)


class EchoDataView(APIView):
    """
    Echoes request post data
    """

    def post(self, request, *args, **kwargs):
        return RestResponse(
            request.data,
            status=status.HTTP_200_OK,
        )


class HealthCheck(APIView):
    """
    Sevice health check.
    """

    def get(self, request, *args, **kwargs):
        # TODO add django-health-check
        response  = None
        try:
            ping, stats = do_health()
        # broad exception to handle all possible error during interaction with MongoDB
        except:
            response = RestResponse(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            if not ('ok' in ping and 'ok' in stats):
                # TODO implement analyzing and return more descriptive response
                response = RestResponse(status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                response = RestResponse(ping, status=status.HTTP_200_OK)

        return response


class OnboardingStatus(APIView):

    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        steps_to_update = request.data.copy()
        user_id = steps_to_update.pop('user_id', None) or request.user.id
        to_update = {
            k: bool(v) for k, v in list(steps_to_update.items()) if k in get_onboarding_steps()
        }
        if to_update and request.user.id:
            projection = {k: 1 for k, v in list(to_update.items())}
            projection['_id'] = 0
            passed_steps = c_onboarding_status().find_one({onboarding.USER_ID: user_id}, projection) or {}
            for step in to_update:
                if to_update[step] and not passed_steps.get(step):
                    create_onboarding_event(
                        event_name='step-completed',
                        created_at=int(time.mktime(time.localtime())),
                        email=request.user.email,
                        metadata={'step': step}
                    )
            c_onboarding_status().update_one({onboarding.USER_ID: user_id}, {'$set': to_update}, upsert=True)
            return RestResponse({'status': 'Ok'}, status=status.HTTP_200_OK)
        return RestResponse({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        data = get_onboarding_status_with_settings(request.user.id)
        if data:
            return RestResponse({'status': 'Ok', 'data': data}, status=status.HTTP_200_OK)


class OnboardingBpAnalysis(APIView):

    authentication_classes = (SessionAuthentication,)

    def post(self, request, *args, **kwargs):
        data = request.data.dict()
        bp_template = BestPracticeTemplate.objects.filter(id=data.pop('best_practice_template_id')).first()
        best_practice = BestPractice.objects.filter(id=data.pop('best_practice_id')).first()
        if bp_template and best_practice:
            data.pop('csrfmiddlewaretoken', None)
            if bp_template.scope == bp_template.COURSELET:
                course_best_practice = best_practice.course.bestpractice_set.filter(
                    template__scope='course', template__slug='practice-exam', courselet=best_practice.courselet
                ).first()
                if course_best_practice and course_best_practice.data:
                    data.update({'base': course_best_practice.data.get('result_data', {}).get('w_courselets')})
                result_data = get_result_courselet_calculation(data, bp_template.calculation)
            else:
                result_data = get_result_course_calculation(data, bp_template.calculation)
            best_practice.data.update({'input_data': data, 'result_data': result_data})
            best_practice.save()
            best_practice.course.apply_from(data, commit=True)
            best_practice.courselet.unit.apply_from(data, commit=True) if best_practice.courselet else None
            return RestResponse({'status': 'Ok', 'result_data': result_data}, status=status.HTTP_200_OK)
        return RestResponse({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


class BestPracticeCreate(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        bp_template = BestPracticeTemplate.objects.filter(id=int(request.POST.get('template_id'))).first()
        data = {}
        if bp_template:
            data["input_data"] = {key: value.get("default") for key, value in bp_template.calculation.items()}
            if bp_template.scope == bp_template.COURSELET:
                data["result_data"] = get_result_courselet_calculation(data["input_data"], bp_template.calculation)
            else:
                data["result_data"] = get_result_course_calculation(data["input_data"], bp_template.calculation)

        try:
            courselet_id = int(request.POST.get('courselet_id')) if request.POST.get('courselet_id') else None
            new_best_practice = BestPractice.objects.create(
                template_id=int(request.POST.get('template_id')),
                course_id=int(request.POST.get('course_id')),
                courselet_id=courselet_id,
                data=data
            )
            if data:
                new_best_practice.data.update(data)
                new_best_practice.save()
                new_best_practice.course.apply_from(data, commit=True)
                new_best_practice.courselet.unit.apply_from(data, commit=True) if new_best_practice.courselet else None
            return RestResponse({'status': 'Ok', 'data': {'new_best_practice': new_best_practice.id}}, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.error(e)
            return RestResponse({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


class BestPracticeUpload(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if request.POST.get('best_practice_id'):
            best_practice = BestPractice.objects.filter(id=int(request.POST.get('best_practice_id'))).first()
            best_practice.upload_file = request.data.get('upload_file')
            best_practice.save()
            create_onboarding_event(
                event_name='exam-upload',
                created_at=int(time.mktime(time.localtime())),
                email=request.user.email,
                metadata={'document-link': best_practice.upload_file.url}
            )
            return RestResponse({'best_practice_id': best_practice.id}, status=status.HTTP_200_OK)
        else:
            try:
                if request.POST.get('template_id'):
                    template_id = int(request.POST.get('template_id'))
                else:
                    template_id = BestPracticeTemplate.objects.filter(slug='upload-practice-exam').first().id
                new_best_practice = BestPractice.objects.create(
                    template_id=template_id,
                    courselet_id=int(request.POST.get('courselet_id')),
                    upload_file=request.data.get('upload_file'),
                    active=True
                )
                create_onboarding_event(
                    event_name='exam-upload',
                    created_at=int(time.mktime(time.localtime())),
                    email=request.user.email,
                    metadata={'document-link': new_best_practice.upload_file.url}
                )
                messages.add_message(
                    self.request,
                    messages.SUCCESS,
                    mark_safe(f"<b>Your document has been uploaded.</b> We’ll send an email to \
                        {self.request.user.email} once it has been converted, usually in a day or two."))
                return RestResponse({'best_practice_id': new_best_practice.id}, status=status.HTTP_200_OK)
            except ValueError as e:
                logger.error(e)
                return RestResponse({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


class CourseletViewSet(viewsets.ModelViewSet):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsInstructor,)
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class CourseletThreadsViewSet(viewsets.ModelViewSet):
    """
    Returns a list of all Courselet's threads.
    """
    authentication_classes = (SessionAuthentication,)
    queryset = UnitLesson.objects.all()
    serializer_class = ThreadSerializer

    def get_unit(self, course_unit_pk):
        """
        Get Unit instanfe from a CoureUnit/Courselet object.
        """
        course_unit = get_object_or_404(CourseUnit, id=course_unit_pk)

        return course_unit.unit

    def get_queryset(self):
        """
        Specifying UniLessons aka Threads for the Courselet aka Unit.
        """
        queryset = super().get_queryset()
        unit = self.get_unit(self.kwargs.get("courselet_pk"))

        return queryset.filter(
            Q(lesson__kind=Lesson.ORCT_QUESTION) | Q(lesson__kind=Lesson.BASE_EXPLANATION),
            unit=unit,
            order__isnull=False)

    def create(self, request, courselet_pk, *args, **kwargs):
        """
        Creates list of Threads for the given Courselet.
        """
        unit = self.get_unit(courselet_pk)
        results = []

        for thread_data in request.data:
            builder = ThreadBuilder(unit)
            ul = builder.build(thread_data)
            result = self.serializer_class(ul).data
            result.update(builder.get_response_data())
            results.append(result)

        return RestResponse(
            {
                "status": "created",
                "result": results
            },
            status=status.HTTP_201_CREATED)

    def update(self, request, courselet_pk, *args, **kwargs):
        """
        Completelly update the Thread with a new data.
        """
        unit = self.get_unit(courselet_pk)
        thread = self.get_object()

        builder = ThreadBuilder(unit)
        undated_thread = builder.update(thread, request.data)

        serializer = self.serializer_class(undated_thread)

        return RestResponse(
            {
                "status": "updated",
                "result": serializer.data
            },
            status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        """
        We need to ensure Lesson instance is deleted.

        Also we have to recalculate an order for a Unit.
        """
        # save Unit to perform reordering
        _unit = instance.unit

        instance.lesson.delete()
        super().perform_destroy(instance)

        _unit.reorder_exercise()


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_courselet_threads(request, pk):
    'test creating a simple GET endpoint'
    course_unit = get_object_or_404(CourseUnit, id=pk)
    if Role.INSTRUCTOR in course_unit.course.get_user_role(request.user, justOne=False, raiseError=False):
        serializer = UnitSerializer2(course_unit.unit)
        return RestResponse(serializer.data)
    else:
        return RestResponse('action is not allowed', status=403)

@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_thread_timecourse(request, pk):
    'return interventions timecourse data for specified thread'
    ul = check_ul_instructor(request, pk)
    serializer = get_ul_serializer(ul, ORCTSerializer3, ULSerializer3)
    data = serializer.data
    data['timenow'] = time.gmtime() # include current timestamp for timediff calculations
    return RestResponse(data)


def check_ul_instructor(request, ulID=None):
    'return UnitLesson iff request.user is course instructor'
    if ulID is None:
        ulID = request.query_params['thread_id']
    ul = get_object_or_404(UnitLesson, id=ulID)
    if Course.objects.filter(role__role=Role.INSTRUCTOR, role__user=request.user,
                             courseunit__unit__unitlesson=ul).exists():
        return ul
    else:
        raise exceptions.PermissionDenied('you are not the instructor')


class NamedViewBase(generics.ListAPIView):
    'base class for creating API endpoint that serves multiple named-views'
    serializer_class = TrivialSerializer
    pagination_class = pagination.LimitOffsetPagination
    def get_queryset(self):
        'apply namedView consisting of filter, order_by, values'
        namedView = self.request.query_params.get('namedView', self._defaultView)
        try:
            nv = self._namedViews[namedView]
        except KeyError:
            raise exceptions.NotFound(f'invalid named view {namedView}')
        if 'filter' in nv:
            queryset = nv['filter'](self)
        else: # use the default filter source
            queryset = self._default_filter()
        if 'order_by' in nv:
            queryset = nv['order_by'](self, queryset)
        return nv['values'](self, queryset)


def response_values_default(self, queryset):
    return queryset.values('id', 'text', 'status', error_id=F('studenterror__errorModel_id'),
                           error_status=F('studenterror__status'), student_firstname=F('author__first_name'),
                           student_lastname=F('author__last_name'), secsPast=timezone.now() - F('atime'))

class ThreadResponsesView(NamedViewBase):
    _namedViews = {
        'StillConfused': {
            'filter': lambda self:self._default_filter().filter(status='help'),
            'order_by': lambda self, queryset: queryset.order_by(Length('text').desc()),
            'values': response_values_default 
        },
        'Latest': {
            'filter': lambda self:self._default_filter(),
            'order_by': lambda self, queryset: queryset.order_by('-atime'),
            'values': response_values_default
        }
    }
    _defaultView = 'StillConfused'
    def _default_filter(self):
        ul = check_ul_instructor(self.request)
        return Response.objects.filter(unitLesson_id=ul.id)


def filter_chats_since(chatStatsView):
    'get Message and Response counts for Chat sessions since startTime'
    if not chatStatsView.request.user or not chatStatsView.request.user.is_superuser:
        raise exceptions.PermissionDenied('you do not have admin rights')
    startTime = chatStatsView.request.query_params.get('startTime', '0')
    startTime = datetime.datetime.fromtimestamp(float(startTime), datetime.timezone.utc)
    return Chat.objects.filter(
              timestamp__gte=startTime,
              is_preview=False
            ).exclude(
              enroll_code__courseUnit__unit__description__contains='newChatMode='
            ).annotate(
              maxtime=Max('message__timestamp')
            ).annotate(
              nresp=Count('message__response_to_check', distinct=True),
              nmsg=Count('message', distinct=True), courselet_id=F('enroll_code__courseUnit_id'),
              duration=F('maxtime') - F('timestamp')
            )

def chats_since_values(self, queryset):
    return queryset.values('id', 'duration', 'nmsg', 'nresp', 'is_open', 'courselet_id', 'timestamp')


def filter_courselet_chats(chatStatsView):
    'get Response counts for Chat sessions in specified courseUnit'
    courseUnit_id = chatStatsView.request.query_params.get('courselet_id', None)
    if not chatStatsView.request.user or courseUnit_id is None or not Role.objects.filter(
            role=Role.INSTRUCTOR, course__courseunit__id=courseUnit_id, 
            user=chatStatsView.request.user).exists():
        raise exceptions.PermissionDenied('you do not have instructor rights')
    return Chat.objects.filter(
              enroll_code__courseUnit_id=courseUnit_id,
              is_preview=False
            ).annotate(
              maxtime=Max('message__timestamp')
            ).annotate(
              nresp=Count('message__response_to_check', distinct=True),
              email=F('user__email'), first_name=F('user__first_name'), last_name=F('user__last_name'),
              duration=F('maxtime') - F('timestamp')
            )


def courselet_chats_values(self, queryset):
    return queryset.values('id', 'duration', 'nresp', 'email', 'first_name', 'last_name', 'timestamp')



class ChatStatsView(NamedViewBase):
    _namedViews = {
        'UsageSince': {
            'filter': filter_chats_since,
            'values': chats_since_values
        },
        'CourseletChats': {
            'filter': filter_courselet_chats,
            'values': courselet_chats_values
        }
    }
    _defaultView = 'UsageSince'


class ThreadErrorsView(generics.ListAPIView):
    serializer_class = StudentErrorSerializer
    def get_queryset(self):
        ul = check_ul_instructor(self.request)
        return StudentError.objects.filter(response__unitLesson=ul)


class InviteView(APIView):
    'API to invite a teacher, student etc. to onboard'
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if self.is_invited_user(request):
            return RestResponse(dict(canInvite=True, invite_types=['teacher', 'parent']),
                                status=status.HTTP_200_OK)
        else:
            return RestResponse(dict(canInvite=False), status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        'needs email address, first_name, last_name, invite_type, enrollCode or course_id'
        page = request.data.get('page', '/')
        data = dict(page=page)
        try:
            invite_type = request.data['invite_type']
        except KeyError:
            return RestResponse('Must specify invite_type', status=status.HTTP_400_BAD_REQUEST)
        messageText = request.data.get('messageText', None)
        try:
            enrollCode = request.data.get('enrollCode', None)
            if enrollCode:
                enrollUnitCode = EnrollUnitCode.objects.get(enrollCode=enrollCode)
                course = enrollUnitCode.courseUnit.course
            else:
                course = Course.objects.get(id=request.data['course_id'])
                enrollUnitCode = None
            instructor = Instructor.objects.get(user=request.user)
        except (Instructor.DoesNotExist, KeyError): # allow invited teacher or parent to invite another
            myInvites = self.is_invited_user(request)
            if myInvites:
                if invite_type in ['teacher', 'parent']: # only allowed to invite teacher or parent
                    enrollUnitCode = EnrollUnitCode.objects.filter(courseUnit__data__onboarding__contains=
                                                                   {invite_type: 'production'}).first()
                    if not enrollUnitCode:
                        enrollUnitCode = EnrollUnitCode.objects.filter(courseUnit__data__has_key='onboarding').first()
                        if not enrollUnitCode:
                            return RestResponse('no onboarding EnrollUnitCode exists',
                                                status=status.HTTP_403_FORBIDDEN)
                    course = enrollUnitCode.courseUnit.course
                    instructor = Instructor.objects.get(user_id=course.addedBy_id)
                else:
                    return RestResponse('invite_type must be teacher or parent',
                                        status=status.HTTP_400_BAD_REQUEST)
            else:
                return RestResponse('only Instructor, invited teacher, or parent can send invitations!',
                                    status=status.HTTP_403_FORBIDDEN)
        if not request.user.is_staff:
            messageText = None # only admin can provide raw text
        invite = Invite.create_new(True, course, instructor, request.data.get('email'),
                                   invite_type, enrollUnitCode, data=data)
        if not invite.user: # need to create inactive account
            password = make_random_password()
            username = invite.get_invited_user_username()
            invite.user = create_unique_user(request.data['email'], password, request.data['first_name'], 
                                             request.data['last_name'], username)
            invite.save()
        else:
            password = None # since user already has account, no need to email their password
            if not invite.user.first_name or not invite.user.last_name: # invitation needs actual name!
                invite.user.first_name = request.data['first_name']
                invite.user.last_name = request.data['last_name']
                invite.user.save()
        invite.send_mail(request.user, password=password, messageText=messageText, request=request,
                         senderName=request.data.get('senderName', None),
                         subjectText=request.data.get('subjectText', None))
        return RestResponse(dict(invite_id=invite.id), status=status.HTTP_201_CREATED)
    def is_invited_user(self, request):
        return Invite.objects.shared_for_me(request).filter(status='joined',
                                                         type__in=['teacher', 'parent']).first()


class ExternalContentHashView(APIView):
    'API to upload a read-only content file such as an image'
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAdminUser,)

    def get(self, request, *args, **kwargs):
        'returns found=list of JSON for hashIDs found; missing=list of hashIDs not found in database'
        hashIDs = request.query_params.getlist('hashID')
        missing = set(hashIDs)
        found = []
        for ech in ExternalContentHash.objects.filter(hashID__in=hashIDs):
            found.append(ECHSerializer(ech).data)
            missing.remove(ech.hashID)
        return RestResponse(dict(found=found, missing=list(missing)), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data
        data['addedBy'] = request.user
        serializer = ECHSerializer(data=data)
        if serializer.is_valid():
            ech = serializer.save()
        return RestResponse(dict(result=serializer.data), status=status.HTTP_201_CREATED)



class CourseContainerView(APIView):
    'API to upload metadata for creating a new Course and its courselets'
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAdminUser,)
    def post(self, request, *args, **kwargs):
        try:
            course = Course(title=request.data['title'], description=request.data['description'], 
                        data=request.data.get('data', None), addedBy=request.user)
            course.save()
            courselets = []
            for i, d in enumerate(request.data.get('units', ())):
                if 'unit_id' in d:
                    unit = Unit.objects.get(id=int(d['unit_id']))
                else:
                    unit = Unit(title=d['title'], description=d['description'], data=d.get('data', None), addedBy=request.user,
                                img_url=d.get('img_url', ''), small_img_url=d.get('small_img_url', ''))
                    unit.save()
                cu = CourseUnit(course=course, unit=unit, order=i, addedBy=request.user)
                cu.save()
                courselets.append(dict(courselet_id=cu.id, unit_id=unit.id))
            return RestResponse(dict(course_id=course.id, courselets=courselets), status=status.HTTP_201_CREATED)
        except Exception as e:
            return RestResponse(dict(error=str(e)), status=status.HTTP_400_BAD_REQUEST)


class Threads2HtmlView(APIView):
    'API to upload Lessons in new text2html + ExternalContentHash format'
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAdminUser,)
    def post(self, request, pk, *args, **kwargs):
        course_unit = get_object_or_404(CourseUnit, id=pk)
        out = []
        for data in request.data:
            data['unit'] = course_unit.unit
            try:
                username = data['addedBy']
            except KeyError: # treat the uploader identity as author
                data['addedBy'] = request.user
            else: # use the specified author identity
                data['addedBy'] = User.objects.get(username=username)
            serializer = Text2HtmlULSerializer(data=data)
            if serializer.is_valid():
                ul = serializer.save()
                out.append(dict(ul_id=ul.id, success=True))
                if getattr(ul, '_answer', False):
                    out[-1]['answer_ul_id'] = ul._answer.id
            else:
                out.append(dict(ul_id=None, success=False))
        return RestResponse(out, status=status.HTTP_201_CREATED)


class AcceptInviteView(APIView):
    'API to accept an invite by providing a validation code'
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAdminUser,)
    def post(self, request, *args, **kwargs):
        'accept Invite by providing its secret code'
        try:
            code = request.data['code']
            email = request.data['email']
            invite = Invite.objects.get(code=code)
        except (KeyError, Invite.DoesNotExist):
            return RestResponse(dict(error='missing or invalid Invite code or email'),
                                status=status.HTTP_400_BAD_REQUEST)
        out = dict(user_id=invite.user.id, invite_id=invite.id)
        try:
            dkimValidation = invite.mailto_acceptance(email, request.data.get('dkimValidation', None),
                                                      request.user.username)
            if dkimValidation:
                out['dkimValidation'] = dkimValidation
        except InviteReplayError as e:
            return RestResponse(dict(error=str(e)), status=status.HTTP_400_BAD_REQUEST)
        return RestResponse(out, status=status.HTTP_201_CREATED)

