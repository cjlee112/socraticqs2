import hashlib
from functools import wraps

from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.utils.encoding import force_bytes
from django.utils.http import urlquote


CACHE_KEY_TEMPLATE = 'views.cache.%s.%s'

pathKwargs = dict(
    courses='course_id',
    units='unit_id',
    lessons='ul_id',
    concepts='ul_id',
    errors='ul_id',
    responses='resp_id',
    nodes='node_id',
)

nameIDs = dict(
    course='course_id',
    unit='unit_id',
    unitLesson='ul_id',
    response='resp_id',
)

def get_path_kwargs(path):
    'extract dict of kwargs from path, suitable for reverse()'
    l = path.split('/')
    kwargs = {}
    for i,k in enumerate(l[:-2]):
        try:
            arg = pathKwargs[k]
            kwargs[arg] = int(l[i + 1])
        except (KeyError,ValueError):
            pass
    return kwargs

# use this as the default arglist: valid for any unitlesson path
unitLessonDefaultArgs = ('course_id', 'unit_id', 'ul_id')
# standard arglists for different types of data
COURSEARGS = ('course_id',)
UNITARGS = ('course_id', 'unit_id')
RESPONSE_ARGS = ('course_id', 'unit_id', 'ul_id', 'resp_id')

# must specify what args each target expects, or reverse() will crash
reverseArgLists = {
    # instructor UI
    'ct:home':(),
    'ct:about':(),
    'ct:person_profile':('user_id',),
    'ct:course':COURSEARGS,
    'ct:edit_course':COURSEARGS,
    'ct:unit_tasks':UNITARGS,
    'ct:unit_concepts':UNITARGS,
    'ct:wikipedia_concept':UNITARGS + ('source_id',),
    'ct:unit_lessons':UNITARGS,
    'ct:unit_resources':UNITARGS,
    'ct:edit_unit':UNITARGS,
    'ct:ul_thread':RESPONSE_ARGS,
    'ct:concept_thread':RESPONSE_ARGS,
    'ct:error_thread':RESPONSE_ARGS,
    'ct:assess_teach':RESPONSE_ARGS,
    # student UI
    'ct:course_student':COURSEARGS,
    'ct:study_unit':UNITARGS,
    'ct:unit_tasks_student':UNITARGS,
    'ct:unit_lessons_student':UNITARGS,
    'ct:unit_concepts_student':UNITARGS,
    'ct:ul_thread_student':RESPONSE_ARGS,
    'ct:concept_thread_student':RESPONSE_ARGS,
    'ct:error_thread_student':RESPONSE_ARGS,
    'ct:assess':RESPONSE_ARGS,
    'ct:assess_errors':RESPONSE_ARGS,
}

def reverse_path_args(target, path, **kwargs):
    'robustly generate desired URL, automatically applying the right IDs'
    pathKwargs = get_path_kwargs(path) # extract IDs from path
    for k,v in kwargs.items():
        if k.endswith('_id'): # use supplied IDs as is
            pathKwargs[k] = v
        elif k in nameIDs: # supply kwargs object IDs too
            pathKwargs[nameIDs[k]] = v.pk
    arglist = reverseArgLists.get(target, unitLessonDefaultArgs)
    reverseArgs = {}
    for k in arglist: # use only the right kwargs for this target
        reverseArgs[k] = pathKwargs[k]
    return reverse(target, kwargs=reverseArgs)


def cache_this(fn):
    """
    Decorator to implement caching on regular function.
    """
    @wraps(fn)
    def wrapped(*args, **kwargs):
        sub_keys = list(args)
        sub_keys.append(kwargs)
        key = ':'.join(urlquote(arg) for arg in sub_keys)
        cache_key = CACHE_KEY_TEMPLATE % (fn.__name__, hashlib.md5(force_bytes(key)).hexdigest())
        result = cache.get(cache_key)

        if not result:
            result = fn(*args, **kwargs)
            # Saving result to cache
            cache.add(cache_key, result)
        return result
    return wrapped
