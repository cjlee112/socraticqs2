try:  # assume we are on production environment
    from prod import *
except ImportError:  # assume we are on developer environment
    from dev import *
