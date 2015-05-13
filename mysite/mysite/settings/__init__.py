try: # assume we are on production environment
    from production_conf import *
except ImportError: # assume we are on developer environment
    from developer_conf import *
