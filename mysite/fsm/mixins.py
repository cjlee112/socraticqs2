import json
import re
from functools import partial

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

WAIT_NODES_REGS = [r"^WAIT_(?!ASSESS$).*$", r"^RECYCLE$"]


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
    is_chat_add_lesson = lambda self: self.fsm.name in ('chat_add_lesson',)

    def get_message(self, chat, current=None, message=None):
        is_additional = chat.state.fsmNode.fsm.name in ['additional', 'resource']
        next_lesson = chat.state.unitLesson
        if self.name == 'LESSON':
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
            _data = {
                'contenttype': 'unitlesson',
                'content_id': next_lesson.id,
                'chat': chat,
                'owner': chat.user,
                'input_type': 'custom',
                'kind': next_lesson.lesson.kind,
                'is_additional': is_additional
            }
            if not self.fsm.name == 'live_chat':
                message = Message.objects.get_or_create(**_data)[0]
            else:
                message = Message(**_data)
                message.save()
        if self.name == 'GET_ANSWER':
            answer = current.get_answers().first()
            _data = {
                'contenttype': 'response',
                'input_type': 'text',
                'lesson_to_answer': current,
                'chat': chat,
                'owner': chat.user,
                'kind': 'response',
                'userMessage': True,
                'is_additional': is_additional
            }
            if not self.fsm.name == 'live_chat':
                message = Message.objects.get_or_create(**_data)[0]
            else:
                message = Message(**_data)
                message.save()
        if self.name == "WAIT_ASSESS":
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

        if self.name == 'ASSESS':
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
        if self.name == 'GET_ASSESS':
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
            if not self.fsm.name == 'live_chat':
                message = Message.objects.get_or_create(**_data)[0]
            else:
                message = Message(**_data)
                message.save()
        if self.name == 'STUDENTERROR':
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
        if self.name == 'RESOLVE':
            message = Message.objects.get_or_create(
                            contenttype='unitlesson',
                            content_id=next_lesson.id,
                            chat=chat,
                            owner=chat.user,
                            input_type='custom',
                            kind='message',
                            timestamp__isnull=True,
                            is_additional=True)[0]
        if self.name == 'MESSAGE_NODE':
            message = Message.objects.get_or_create(
                            chat=chat,
                            owner=chat.user,
                            text=chat.state.fsmNode.title,
                            student_error=message.student_error,
                            input_type='custom',
                            kind='message',
                            is_additional=True)[0]
        if self.name in ['END', 'IF_RESOURCES']:
            if not self.help:
                text = self.get_help(chat.state, request=None)
            else:
                text = self.help
            message = Message.objects.get_or_create(
                            chat=chat,
                            owner=chat.user,
                            text=text,
                            input_type='custom',
                            kind='message',
                            is_additional=True)[0]
        if self.name == 'GET_RESOLVE':
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
        if self.name == 'ERRORS':
            message = Message.objects.get_or_create(
                            chat=chat,
                            owner=chat.user,
                            text='''Below are some common misconceptions. '''
                                 '''Select one or more that is similar to your reasoning.''',
                            kind='message',
                            input_type='custom',
                            is_additional=is_additional)[0]
        if self.name == 'GET_ERRORS':
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
        if self.name == 'TITLE':
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
        if self.name == 'START_MESSAGE':
            message = Message.objects.create(
                            input_type='options',
                            text=self.title,
                            chat=chat,
                            owner=chat.user,
                            kind='button',
                            is_additional=is_additional)
        if self.name == 'DIVIDER':
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

        if self.name == 'START' and self.fsm.name in('live_chat',):
            message = Message.objects.get_or_create(
                chat=chat,
                text=self.title,
                kind='button',
                is_additional=is_additional,
                owner=chat.user,
            )[0]


        if self.name in ('GET_UNIT_NAME_TITLE', 'GET_UNIT_QUESTION', 'GET_UNIT_ANSWER', 'GET_HAS_UNIT_ANSWER'):
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

        if self.name in ('START', 'WELL_DONE') and self.is_chat_add_lesson():
            text = "<b>{}</b><br>{}".format(self.title, getattr(self, 'help', '') or '')
            _data = dict(
                chat=chat,
                text=text,
                input_type='custom',
                kind='message',
                is_additional=is_additional,
                owner=chat.user,
            )
            message = Message.objects.create(**_data)

        if self.name in ('UNIT_QUESTION',) and self.is_chat_add_lesson():
            text = "<b>{}</b><br>{}".format(self.title, getattr(self, 'help', '') or '')
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

        if self.name in ('HAS_UNIT_ANSWER',):
            _data = dict(
                chat=chat,
                text=self.title,
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

        # if self.name == 'GET_HAS_UNIT_ANSWER':
        #     _data = dict(
        #         chat=chat,
        #         text='',
        #         input_type='text',
        #         kind='response',
        #         owner=chat.user,
        #         userMessage=True,
        #         is_additional=is_additional
        #     )
        #     # _data = dict(
        #     #     contenttype='unitlesson',
        #     #     response_to_check=response_to_chk,
        #     #     input_type='custom',
        #     #     content_id=answer.id,
        #     #     chat=chat,
        #     #     owner=chat.user,
        #     #     kind=answer.kind,
        #     #     is_additional=is_additional)
        #     if message and message.content_id:
        #         _data['content_id'] = message.content_id
        #         _data['contenttype'] = 'unitlesson'
        #     message = Message.objects.get_or_create(**_data)[0]


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
