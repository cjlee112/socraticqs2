from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from mysite.decorators import not_anonymous_required


class NewLoginRequiredMixin(object):
    """
    Ensures that user must be authenticated in order to access view.
    """
    @method_decorator(login_required(login_url='new_login'))
    def dispatch(self, *args, **kwargs):
        return super(NewLoginRequiredMixin, self).dispatch(*args, **kwargs)


class LoginRequiredMixin(object):
    """
    Ensures that user must be authenticated in order to access view.
    """
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class NotAnonymousRequiredMixin(LoginRequiredMixin):
    @method_decorator(not_anonymous_required)
    def dispatch(self, *args, **kwargs):
        return super(NotAnonymousRequiredMixin, self).dispatch(*args, **kwargs)
