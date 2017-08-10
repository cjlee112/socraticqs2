from django import forms
from ct.models import Response, Course, Unit, Concept, Lesson, ConceptLink, ConceptGraph, STATUS_CHOICES, StudentError, UnitLesson
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
## from crispy_forms.bootstrap import StrictButton


class ResponseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ResponseForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-responseForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', 'Save'))
    class Meta:
        model = Response
        fields = ['text', 'confidence']
        labels = dict(text=_('Your answer'))

class CommentForm(ResponseForm):
    class Meta:
        model = Response
        fields = ['title', 'text', 'confidence']
        labels = dict(text=_('Your question'),
                      confidence=_('How do you feel about this?'))

class ReplyForm(ResponseForm):
    class Meta:
        model = Response
        fields = ['title', 'text', 'confidence']
        labels = dict(text=_('Your reply'),
                      confidence=_('How do you feel about this?'))

class ErrorStatusForm(ResponseForm):
    class Meta:
        model = StudentError
        fields = ['status']
        labels = dict(status=_('How well have you overcome this error?'))

class SelfAssessForm(forms.Form):
    selfeval = forms.ChoiceField(choices=(('', '----'),) + Response.EVAL_CHOICES,
                label='How does this answer compare with the right answer?')
    status = forms.ChoiceField(choices=(('', '----'),) + STATUS_CHOICES,
                label='How well do you feel you understand this concept now?')
    liked = forms.BooleanField(required=False,
                label='''Check here if this lesson really showed
                you something you were missing before.''')
    def __init__(self, *args, **kwargs):
        super(SelfAssessForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-selfAssessForm'
        self.helper.form_class = 'form-vertical'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Next'))

class AssessErrorsForm(forms.Form):
    emlist = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                       required=False, label='Common errors')

class ReorderForm(forms.Form):
    newOrder = forms.ChoiceField()
    oldOrder = forms.CharField()
    def __init__(self, initial, total, *args, **kwargs):
        super(ReorderForm, self).__init__(*args, **kwargs)
        self.fields['newOrder'].initial = str(initial)
        self.fields['newOrder'].choices = [(str(i),str(i + 1))
                                           for i in range(total)]


class NextLikeForm(forms.Form):
    liked = forms.BooleanField(required=False,
                label='''Check here if this lesson really showed
                you something you were missing before.''')
    def __init__(self, *args, **kwargs):
        super(NextLikeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-nextlikeForm'
        self.helper.form_class = 'form-vertical'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Next'))


class NextForm(forms.Form):
    fsmtask = forms.CharField(widget=forms.HiddenInput)
    def __init__(self, label='Next', fsmtask='next', submitArgs={},
                 *args, **kwargs):
        super(NextForm, self).__init__(*args, **kwargs)
        self.fields['fsmtask'].initial = fsmtask
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-nextForm'
        self.helper.form_class = 'form-vertical'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', label, **submitArgs))

class LaunchFSMForm(NextForm):
    fsmName = forms.CharField(widget=forms.HiddenInput)
    def __init__(self, fsmName, label, fsmtask='launch',
                 *args, **kwargs):
        super(LaunchFSMForm, self).__init__(label, fsmtask, *args, **kwargs)
        self.fields['fsmName'].initial = fsmName

class TaskForm(forms.Form):
    task = forms.CharField(widget=forms.HiddenInput)
    def __init__(self, task='start', label='Start', *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['task'].initial = task
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-startForm'
        self.helper.form_class = 'form-vertical'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', label))

class LessonRoleForm(forms.Form):
    role = forms.ChoiceField(choices=UnitLesson.ROLE_CHOICES,
                             label='Role of this lesson in this courselet:')
    def __init__(self, initial=UnitLesson.LESSON_ROLE, *args, **kwargs):
        super(LessonRoleForm, self).__init__(*args, **kwargs)
        self.fields['role'].initial = initial
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-startForm'
        self.helper.form_class = 'form-vertical'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Change Role'))


class ResponseListForm(forms.Form):
    ndisplay = forms.ChoiceField(choices=(('25', '25'), ('50', '50'),
                                          ('100', '100')))
    sortOrder = forms.ChoiceField(choices=(('-atime', 'Most recent first'),
                                           ('atime', 'Least recent first'),
                                           ('-confidence', 'Most confident first'),
                                           ('confidence', 'Least confident first')))

class UnitTitleForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(UnitTitleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-unitTitleForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = Unit
        fields = ['title', 'description', 'img_url', 'small_img_url']

class NewUnitTitleForm(UnitTitleForm):
    submitLabel = 'Add'

class CourseTitleForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(CourseTitleForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-courseTitleForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = Course
        fields = ['title', 'access', 'description']

class NewCourseTitleForm(CourseTitleForm):
    submitLabel = 'Add'

class ConceptForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(ConceptForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-conceptForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = Concept
        fields = ['title']

class NewConceptForm(forms.Form):
    title = forms.CharField()
    description = forms.CharField(widget=forms.Textarea)
    submitLabel = 'Add'
    def __init__(self, *args, **kwargs):
        super(NewConceptForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-conceptForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))

class ConceptSearchForm(forms.Form):
    search = forms.CharField(label='Search for concepts containing')

class ConceptLinkForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(ConceptLinkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-conceptLinkForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = ConceptLink
        fields = ['relationship']

class ConceptGraphForm(forms.ModelForm):
    submitLabel = 'Update'
    def __init__(self, *args, **kwargs):
        super(ConceptGraphForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-conceptGraphForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = ConceptGraph
        fields = ['relationship']

class NewErrorForm(forms.ModelForm):
    submitLabel = 'Add'
    def __init__(self, *args, **kwargs):
        super(NewErrorForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-errorForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', self.submitLabel))
    class Meta:
        model = Lesson
        fields = ['title', 'text']

class ErrorForm(NewErrorForm):
    submitLabel = 'Update'
    changeLog = forms.CharField(required=False,
            label='Commit Message (to commit a snapshot to your version history, summarize changes made since the last snapshot)')
    class Meta:
        model = Lesson
        fields = ['title', 'text', 'changeLog']

class LessonForm(ErrorForm):
    url = forms.CharField(required=False)
    class Meta:
        model = Lesson
        fields = ['title', 'kind', 'text', 'medium', 'add_unit_aborts', 'url', 'changeLog']
        labels = dict(kind=_('Lesson Type'), medium=_('Delivery medium'))

class AnswerLessonForm(LessonForm):
    class Meta:
        model = Lesson
        fields = ['title', 'text', 'medium', 'url', 'changeLog']
        labels = dict(medium=_('Delivery medium'))

class NewLessonForm(NewErrorForm):
    submitLabel = 'Add'
    url = forms.CharField(required=False)
    class Meta:
        model = Lesson
        fields = ['title', 'kind', 'text', 'medium', 'url']
        labels = dict(kind=_('Lesson Type'), medium=_('Delivery medium'))

class ResponseFilterForm(forms.Form):
    selfeval = forms.ChoiceField(required=False, initial=Response.DIFFERENT,
                choices=(('', '----'),) + Response.EVAL_CHOICES[:2])
    status = forms.ChoiceField(required=False,
                choices=(('', '----'),) + STATUS_CHOICES)
    confidence = forms.ChoiceField(required=False,
                choices=(('', '----'),) + Response.CONF_CHOICES)


class SearchFormBase(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SearchFormBase, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-lessonSearchForm'
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
    ##    self.helper.field_template = 'bootstrap3/layout/inline_field.html'
        self.helper.add_input(Submit('submit', 'Search'))
    ##    self.helper.add_input(StrictButton('Search', css_class='btn-default'))
    ## sourceDB = forms.ChoiceField(choices=(('wikipedia', 'Wikipedia'),),
    ##                              label='Search Courselets.org and')

class LessonSearchForm(SearchFormBase):
    searchType = forms.ChoiceField(choices=(('lesson', 'lessons'),
                                      ('question', 'questions'),),
                             label='Search for')
    search = forms.CharField(label='containing')

class ErrorSearchForm(SearchFormBase):
    search = forms.CharField(label='Search for errors containing')

class LogoutForm(forms.Form):
    task = forms.CharField(initial='logout', widget=forms.HiddenInput)
    def __init__(self, *args, **kwargs):
        super(LogoutForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-logoutForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', 'Sign out'))

class CancelForm(forms.Form):
    task = forms.CharField(initial='abort', widget=forms.HiddenInput)
    def __init__(self, *args, **kwargs):
        super(CancelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'id-cancelForm'
        self.helper.form_class = 'form-vertical'
        self.helper.add_input(Submit('submit', 'Cancel this Activity'))


###############################################################
# utility functions

def set_crispy_action(actionTarget, *forms):
    'set the form.helper.form_action for one or more forms'
    for form in forms:
        form.helper.form_action = actionTarget


class BaseForm(forms.ModelForm):
    """
    Base class for admin forms.
    """
    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)

        for field_name in ('addedBy', 'author'):
            if field_name in self.fields and not self.initial.get(field_name):
                self.initial[field_name] = self.current_user
