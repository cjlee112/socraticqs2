"""
Utils for FSM application.
"""


def get_plugin(funcName):
    """
    Import and call plugin func for this object.
    """
    import importlib
    if not funcName:
        raise ValueError('invalid call_plugin() with no funcName!')
    i = funcName.rindex('.')
    modName = funcName[:i]
    funcName = funcName[i + 1:]
    mod = importlib.import_module(modName)
    return getattr(mod, funcName)
