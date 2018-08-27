import json
import re
from functools import partial

from pymongo.errors import ConnectionFailure

from ct.models import (
    Role,
    Unit,
    Course,
    Lesson,
    Concept,
    Response,
    CourseUnit,
    UnitStatus,
    UnitLesson,
    ConceptLink,
    StudentError,
    ConceptGraph
)
from chat.models import Message, ChatDivider, UnitError
from grading.base_grader import GRADERS
from core.common.mongo import c_chat_stack


WAIT_NODES_REGS = [r"^WAIT_(?!ASSESS$).*$", r"^RECYCLE$"]
QUESTION_STACK_PATTERN = 'question_stack:uid:{}:chat_id:{}'


def is_wait_node(name):
    return any(
        map(partial(re.search, string=name), WAIT_NODES_REGS)
    )


# index of types that can be saved in json blobs
KLASS_NAME_DICT = dict(
    Unit=Unit,
    Role=Role,
    Course=Course,
    Lesson=Lesson,
    Concept=Concept,
    Response=Response,
    UnitLesson=UnitLesson,
    ConceptLink=ConceptLink,
    ConceptGraph=ConceptGraph,
    StudentError=StudentError,
    CourseUnit=CourseUnit,
    UnitStatus=UnitStatus,
)


SIMILAR_KINDS = (Lesson.BASE_EXPLANATION, Lesson.EXPLANATION)


class JSONBlobMixin(object):
    """
    Mixin to dump/load data to/from JSON blob fields.
    """
    @staticmethod
    def dump_json_id(obj, name=None):
        """
        Produce tuple of form ("NAME_Response_id", obj.pk).
        """
        _list = []
        if name:
            _list.append(name)
        name = '_'.join(_list + [obj.__class__.__name__, 'id'])
        return (name, obj.pk)

    def dump_json_id_dict(self, state_data):
        """
        Get json representation of dict of db objects.
        """
        data = {}
        for key, value in state_data.items():
            if value.__class__.__name__ in KLASS_NAME_DICT:  # save db object id
                name, pk = self.dump_json_id(value, key)
                data[name] = pk
            else:  # just copy literal value, assuming JSON can serialize it
                data[key] = value
        return json.dumps(data)

    def save_json_data(self, state_data=None, attr='data', doSave=True):
        """
        Save dict of object refs back to db blob field.
        """
        dict_attr = '_%s_dict' % attr
        if state_data is None:  # save cached data
            state_data = getattr(self, dict_attr)
        else:  # save specified dict
            setattr(self, dict_attr, state_data)  # cache on local object
        if state_data:
            dumped_state_data = self.dump_json_id_dict(state_data)
        else:
            dumped_state_data = None
        setattr(self, attr, dumped_state_data)
        if doSave:  # immediately write to db
            self.save()

    @staticmethod
    def load_json_id(name, pk):
        """
        Get the specified object as (label, obj) tuple.
        """
        splitted_name = name.split('_')
        klass_name = splitted_name[-2]
        obj = KLASS_NAME_DICT[klass_name].objects.get(pk=pk)
        return (splitted_name[0], obj)

    def load_json_id_dict(self, state_data):
        """
        Get dict of db objects from json blob representation.
        """
        data = json.loads(state_data)
        obj_dict = {}
        for key, value in data.items():
            if key.endswith('_id'):  # retrieve db object
                name, obj = self.load_json_id(key, value)
                obj_dict[name] = obj
            else:  # just copy literal value
                obj_dict[key] = value
        return obj_dict

    def load_json_data(self, attr='data'):
        """
        Get dict of db objects from json blob field.
        """
        dict_attr = '_%s_dict' % attr
        try:
            return getattr(self, dict_attr)
        except AttributeError:
            pass
        state_data = getattr(self, attr)
        if state_data:
            obj_dict = self.load_json_id_dict(state_data)
        else:
            obj_dict = {}
        setattr(self, dict_attr, obj_dict)
        return obj_dict

    def set_data_attr(self, attr, value):
        """Set a single data attribute

        Must later call save_json_data() to serialize.
        """
        obj_dict = self.load_json_data()
        obj_dict[attr] = value

    def get_data_attr(self, attr):
        """
        Get a single data attribute from json data.
        """
        obj_dict = self.load_json_data()
        try:
            return obj_dict[attr]
        except KeyError:
            raise AttributeError('JSON data has no attr %s' % attr)


class ChatMixin(object):
    """
    Allow to create message based on current FSM node type.
    """
    def node_name_is_one_of(self, *args):
        return self.name in args

    def get_message(self, chat, request, current=None, message=None):
        stack_pattern = QUESTION_STACK_PATTERN.format(request.user.id, chat.id)
        is_additional = chat.state.fsmNode.fsm.fsm_name_is_one_of('additional', 'resource')
        next_lesson = chat.state.unitLesson
        if self.node_name_is_one_of('LESSON'):
            input_type = 'custom'
            kind = next_lesson.lesson.kind
            try:
                if is_additional:
                    raise UnitLesson.DoesNotExist
                unitStatus = chat.state.get_data_attr('unitStatus')
                next_ul = unitStatus.unit.unitlesson_set.get(order=unitStatus.order+1)
                if next_ul and next_ul.lesson.kind in SIMILAR_KINDS and kind in SIMILAR_KINDS:
                    input_type = 'options'
                    kind = 'button'
            except UnitLesson.DoesNotExist:
                pass
            message = Message.objects.get_or_create(
                contenttype='unitlesson',
                content_id=next_lesson.id,
                chat=chat,
                owner=chat.user,
                input_type=input_type,
                kind=kind,
                is_additional=is_additional)[0]
        if self.name == 'ASK':
            SUB_KIND_TO_KIND_MAP = {
                'choices': 'button',
            }
            SUBKIND_TO_INPUT_TYPE_MAP = {
                'choices': 'options',
            }
            sub_kind = next_lesson.lesson.sub_kind
            _data = {
                'contenttype': 'unitlesson',
                'content_id': next_lesson.id,
                'chat': chat,
                'owner': chat.user,
                'input_type': 'custom', # SUBKIND_TO_INPUT_TYPE_MAP.get(sub_kind, 'custom'),
                'kind': next_lesson.lesson.kind,  # SUB_KIND_TO_KIND_MAP.get(sub_kind, next_lesson.lesson.kind),
                'is_additional': is_additional
            }
            if not self.fsm.fsm_name_is_one_of('live_chat'):
                message = Message.objects.get_or_create(**_data)[0]
            else:
                message = Message(**_data)
                message.save()

            find_crit = {
                "stack_id": stack_pattern
            }
            # TODO: remove print after complete the task
            print('Pushing to {} value: {}'.format(stack_pattern, next_lesson.id))
            c_chat_stack().update_one(
                find_crit,
                {"$push": {"stack": next_lesson.id}},
                upsert=True)
            # Fallback method to pass ul_id's throught messages
            if request.session.get(stack_pattern):
                if isinstance(request.session[stack_pattern], list):
                    request.session[stack_pattern].append(next_lesson.id)
                else:
                    request.session[stack_pattern] = [request.session[stack_pattern]]
                    request.session[stack_pattern].append(next_lesson.id)
            else:
                request.session[stack_pattern] = [next_lesson.id]
        if self.node_name_is_one_of('ABORTS', 'GET_ABORTS'):
            message = Message.objects.create(
                owner=chat.user,
                chat=chat,
                kind='message',
                input_type='custom',
                is_additional=is_additional,
                text=self.name
            )
        if self.node_name_is_one_of('GET_ANSWER'):
            # TODO: remove print after complete the task
            print('Getting the session data: {}'.format(stack_pattern))
            print('From session: {}'.format(request.session.get(stack_pattern)))
            find_crit = {
                "stack_id": stack_pattern
            }
            stack = None
            try:
                document = c_chat_stack().find_and_modify(
                    query=find_crit,
                    update={"$pop": {"stack": 1}})
                stack = document.get('stack', [])
            except ConnectionFailure:
                pass
            if request.session.get(stack_pattern):
                if isinstance(request.session[stack_pattern], list):
                    fallback_ul_id = request.session[stack_pattern].pop()
                elif isinstance(request.session[stack_pattern], int):
                    fallback_ul_id = request.session[stack_pattern]
                else:
                    fallback_ul_id = current.id
            unit_lesson_id = stack.pop() if stack else fallback_ul_id
            # TODO: remove print after complete the task
            print('UL_ID: {}'.format(unit_lesson_id))
            lesson_to_answer = UnitLesson.objects.filter(id=unit_lesson_id).first()
            _data = {
                'contenttype': 'response',
                'input_type': 'text',
                'lesson_to_answer': lesson_to_answer,
                'chat': chat,
                'owner': chat.user,
                'kind': 'response',
                'userMessage': True,
                'is_additional': is_additional
            }
            if lesson_to_answer.lesson.sub_kind == 'choices':
                _data.update(dict(
                    input_type='options',

                ))

            if not self.fsm.fsm_name_is_one_of('live_chat'):
                message = Message.objects.get_or_create(**_data)[0]
            else:
                message = Message(**_data)
                message.save()
        if self.node_name_is_one_of('CONFIDENCE'):
            # current here is Response instance
            if isinstance(current, Response):
                response_to_chk = current
                answer = current.unitLesson.get_answers().first()
            else:
                response_to_chk = message.response_to_check
                if not message.lesson_to_answer:
                    answer = message.response_to_check.unitLesson.get_answers().first()
                else:
                    answer = message.lesson_to_answer.get_answers().first()
            message = Message.objects.create(  # get_or_create
                contenttype='unitlesson',
                response_to_check=response_to_chk,
                input_type='custom',
                text=self.title,
                chat=chat,
                owner=chat.user,
                kind=answer.kind,
                is_additional=is_additional)
        if self.node_name_is_one_of('GET_CONFIDENCE'):
            _data = dict(
                contenttype='response',
                content_id=message.response_to_check.id,
                input_type='options',
                chat=chat,
                owner=chat.user,
                kind='response',
                userMessage=True,
                is_additional=is_additional,
            )
            # here was Message.objects.create for all fsm's except live_chat. for live_chat fsm here was get_or_create
            message = Message(**_data)
            message.save()
        if self.node_name_is_one_of("WAIT_ASSESS"):
            if isinstance(current, Response):
                resp_to_chk = current
            else:
                resp_to_chk = message.response_to_check
            message = Message.objects.get_or_create(
                chat=chat,
                text=self.title,
                kind='button',
                response_to_check=resp_to_chk,
                is_additional=is_additional,
                owner=chat.user,
            )[0]

        if self.node_name_is_one_of('ASSESS'):
            # current here is Response instance
            if isinstance(current, Response):
                response_to_chk = current
                answer = current.unitLesson.get_answers().first()
            else:
                response_to_chk = message.response_to_check
                if not message.lesson_to_answer:
                    answer = message.response_to_check.unitLesson.get_answers().first()
                else:
                    answer = message.lesson_to_answer.get_answers().first()
            message = Message.objects.get_or_create(
                contenttype='unitlesson',
                response_to_check=response_to_chk,
                input_type='custom',
                content_id=answer.id,
                chat=chat,
                owner=chat.user,
                kind=answer.kind,
                is_additional=is_additional)[0]
        if self.node_name_is_one_of('GET_ASSESS'):
            _data = dict(
                contenttype='response',
                content_id=message.response_to_check.id,
                input_type='options',
                chat=chat,
                owner=chat.user,
                kind='response',
                userMessage=True,
                is_additional=is_additional
            )
            # here was Message.objects.create for all fsm's except live_chat. for live_chat fsm here was get_or_create
            message = Message(**_data)
            message.save()

        if self.node_name_is_one_of('GRADING'):
            GraderClass = GRADERS.get(message.content.unitLesson.lesson.sub_kind)
            if GraderClass:
                grader = GraderClass(message.content.unitLesson, message.content)
                # grade method must be called to actually do the work
                grader.grade
                text = 'Your answer is {}!'.format(grader.message)
            else:
                text = "No such grader! Grading could not be applied."
            message = Message.objects.create(
                owner=chat.user,
                chat=chat,
                kind='message',
                input_type='custom',
                is_additional=is_additional,
                text=text
            )

        if self.node_name_is_one_of('STUDENTERROR'):
            resolve_message = Message.objects.get(
                            contenttype='unitlesson',
                            content_id=next_lesson.id,
                            chat=chat,
                            owner=chat.user,
                            input_type='custom',
                            kind='message',
                            timestamp__isnull=True,
                            is_additional=True)
            message = Message.objects.get_or_create(
                            contenttype='unitlesson',
                            content_id=resolve_message.student_error.errorModel.id,
                            chat=chat,
                            owner=chat.user,
                            student_error=resolve_message.student_error,
                            input_type='options',
                            kind='button',
                            is_additional=True)[0]
        if self.node_name_is_one_of('RESOLVE'):
            message = Message.objects.get_or_create(
                            contenttype='unitlesson',
                            content_id=next_lesson.id,
                            chat=chat,
                            owner=chat.user,
                            input_type='custom',
                            kind='message',
                            timestamp__isnull=True,
                            is_additional=True)[0]
        if self.node_name_is_one_of('MESSAGE_NODE'):
            message = Message.objects.get_or_create(
                            chat=chat,
                            owner=chat.user,
                            text=chat.state.fsmNode.title,
                            student_error=message.student_error,
                            input_type='custom',
                            kind='message',
                            is_additional=True)[0]
        if self.node_name_is_one_of('END', 'IF_RESOURCES'):
            if not self.help:
                text = self.get_help(chat.state, request=None)
            else:
                text = self.help
            message = Message.objects.create(
                            chat=chat,
                            owner=chat.user,
                            text=text,
                            input_type='custom',
                            kind='message',
                            is_additional=True)
        if self.node_name_is_one_of('GET_RESOLVE'):
                message = Message.objects.create(
                            contenttype='unitlesson',
                            content_id=next_lesson.id,
                            input_type='options',
                            chat=chat,
                            owner=chat.user,
                            student_error=message.student_error,
                            kind='response',
                            userMessage=True,
                            is_additional=is_additional)
        if self.node_name_is_one_of('ERRORS'):
            message = Message.objects.get_or_create(
                            chat=chat,
                            owner=chat.user,
                            text='''Below are some common misconceptions. '''
                                 '''Select one or more that is similar to your reasoning.''',
                            kind='message',
                            input_type='custom',
                            is_additional=is_additional)[0]
        if self.node_name_is_one_of('GET_ERRORS'):
            uniterror = UnitError.get_by_message(message)
            message = Message.objects.get_or_create(
                            contenttype='uniterror',
                            content_id=uniterror.id,
                            input_type='options',
                            chat=chat,
                            kind='uniterror',
                            owner=chat.user,
                            userMessage=False,
                            is_additional=is_additional)[0]
        if self.node_name_is_one_of('TITLE'):
            divider = ChatDivider(text=next_lesson.lesson.title,
                                  unitlesson=next_lesson)
            divider.save()
            message = Message.objects.get_or_create(
                            contenttype='chatdivider',
                            content_id=divider.id,
                            input_type='custom',
                            type='breakpoint',
                            chat=chat,
                            owner=chat.user,
                            kind='message',
                            is_additional=is_additional)[0]
        if self.node_name_is_one_of('START_MESSAGE'):
            message = Message.objects.create(
                            input_type='options',
                            text=self.title,
                            chat=chat,
                            owner=chat.user,
                            kind='button',
                            is_additional=is_additional)
        if self.node_name_is_one_of('DIVIDER'):
            divider = ChatDivider(text=self.title)
            divider.save()
            message = Message.objects.get_or_create(
                            contenttype='chatdivider',
                            content_id=divider.id,
                            input_type='custom',
                            type='breakpoint',
                            chat=chat,
                            owner=chat.user,
                            kind='message',
                            is_additional=is_additional)[0]

        if self.node_name_is_one_of('START') and self.fsm.fsm_name_is_one_of('live_chat'):
            message = Message.objects.get_or_create(
                chat=chat,
                text=self.title,
                kind='button',
                is_additional=is_additional,
                owner=chat.user,
            )[0]

        if self.name in (
                'GET_UNIT_NAME_TITLE',
                'GET_UNIT_QUESTION',
                'GET_UNIT_ANSWER',
                'GET_HAS_UNIT_ANSWER',
        ):
            _data = dict(
                chat=chat,
                owner=chat.user,
                input_type='text',
                kind='response',
                userMessage=True,
                is_additional=is_additional
            )
            if isinstance(current, UnitLesson):
                _data['content_id'] = current.id
                # _data['text'] = current.lesson.title
                _data['contenttype'] = 'unitlesson'
            elif message and message.content:
                # _data['text'] = "current.lesson"
                _data['content_id'] = message.content_id
                _data['contenttype'] = message.contenttype

            # content_id = current.id if current else None
            message = Message.objects.create(**_data)

        if self.name in ('START', 'UNIT_NAME_TITLE', 'NOT_A_QUESTION') and self.fsm.fsm_name_is_one_of('chat_add_lesson'):
            text = "**{}** \n\n{}".format(self.title, getattr(self, 'help', '') or '')
            _data = dict(
                chat=chat,
                text=text,
                input_type='custom',
                kind='message',
                is_additional=is_additional,
                owner=chat.user,
            )
            message = Message.objects.create(**_data)

        if self.name in ('UNIT_QUESTION', 'UNIT_ANSWER') and self.fsm.fsm_name_is_one_of('chat_add_lesson'):
            text = "**{}** \n\n{}".format(self.title, getattr(self, 'help', '') or '')
            _data = dict(
                chat=chat,
                text=text,
                input_type='custom',
                kind='message',
                is_additional=is_additional,
                owner=chat.user,
            )
            # import ipdb; ipdb.set_trace()
            if message and message.content_id:
                _data['content_id'] = message.content_id
                _data['contenttype'] = 'unitlesson'
            elif isinstance(current, UnitLesson):
                _data['content_id'] = current.id
                _data['contenttype'] = 'unitlesson'
            message = Message.objects.create(**_data)

        if self.name in ('HAS_UNIT_ANSWER', 'WELL_DONE'):
            text = "**{}** \n\n{}".format(self.title, getattr(self, 'help', '') or '')
            _data = dict(
                chat=chat,
                text=text,
                input_type='options',
                kind='message',
                owner=chat.user,
                userMessage=False,
                is_additional=is_additional
            )
            if message and message.content_id:
                _data['content_id'] = message.content_id
                _data['contenttype'] = 'unitlesson'
            message = Message.objects.create(**_data)

        if self.name in ('WELL_DONE',):
            text = "**{}** \n\n{}".format(self.title, getattr(self, 'help', '') or '')
            _data = dict(
                chat=chat,
                text=text,
                input_type='options',
                kind='button',
                owner=chat.user,
                userMessage=False,
                is_additional=is_additional
            )
            if message and message.content_id:
                _data['content_id'] = message.content_id
                _data['contenttype'] = 'unitlesson'
            message = Message.objects.create(**_data)

        # wait for RECYCLE node and  any node starting from WAIT_ except WAIT_ASSESS
        if is_wait_node(self.name):
            lookup = dict(
                chat=chat,
                text=self.title,
                kind='button',
                is_additional=False,
                owner=chat.user
            )
            message = Message.objects.get_or_create(**lookup)[0]
        return message
