import json

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

    def get_message(self, chat, current=None, message=None):
        print "Current node is " + self.name
        next_lesson = chat.state.unitLesson
        if self.name == 'LESSON':
            message = Message(contenttype='unitlesson',
                              content_id=next_lesson.id,
                              chat=chat,
                              owner=chat.user,
                              input_type='custom',
                              kind=next_lesson.lesson.kind)
        if self.name == 'ASK':
            message = Message(contenttype='unitlesson',
                              content_id=next_lesson.id,
                              input_type='custom',
                              chat=chat,
                              kind=next_lesson.lesson.kind,
                              owner=chat.user)
        if self.name == 'ASSESS':
            answer = current.unitLesson.get_answers().first()
            message = Message(contenttype='unitlesson',
                              response_to_check=current,
                              input_type='custom',
                              content_id=current.unitLesson.get_answers().first().id,
                              chat=chat,
                              owner=chat.user,
                              kind=answer.kind)
        if self.name == 'ERRORS':
            message = Message(chat=chat,
                              owner=chat.user,
                              type='breakpoint',
                              text='Below are some common misconceptions. Select one or more that is similar to your reasoning.',
                              kind='message',
                              input_type='custom',
                              )
        if self.name == 'END':
            divider = ChatDivider(text=self.title)
            divider.save()
            message = Message(contenttype='chatdivider',
                              content_id=divider.id,
                              input_type='finish',
                              type='breakpoint',
                              chat=chat,
                              owner=chat.user,
                              kind='message',)
        message.save()
        return message
