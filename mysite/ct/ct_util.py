from django.core.urlresolvers import reverse


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
        except KeyError:
            pass
    return kwargs

# use this as the default arglist: valid for any unitlesson path
unitLessonDefaultArgs = ('course_id', 'unit_id', 'ul_id')
# standard arglists for different types of data
UNITARGS = ('course_id', 'unit_id')

# must specify what args each target expects, or reverse() will crash
reverseArgLists = {
    'ct:home':(),
    'ct:about':(),
    'ct:unit_lessons':UNITARGS,
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
