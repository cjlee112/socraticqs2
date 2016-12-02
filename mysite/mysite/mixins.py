from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator


class LoginRequiredMixin(object):

    u"""Ensures that user must be authenticated in order to access view."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)

    # @classmethod
    # def as_view(cls, **initkwargs):
    #     view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
    #     return login_required(view, login_url=reverse_lazy('login'))
