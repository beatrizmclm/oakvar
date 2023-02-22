from typing import Optional


def exampleinput(directory: Optional[str] = ".", outer=None):
    """exampleinput.

    Args:
        directory (Optional[str]): directory
        outer:
    """
    from ..lib.util.admin_util import fn_new_exampleinput

    if not directory:
        return
    ret = fn_new_exampleinput(directory)
    if outer:
        outer.write(ret)
    return ret


def module(name: Optional[str] = None, type: Optional[str] = None):
    """module.

    Args:
        name (Optional[str]): name
        type (Optional[str]): type
    """
    from ..lib.util.admin_util import create_new_module
    from ..lib.module.local import get_local_module_info

    if not name or not type:
        return None
    create_new_module(name, type)
    module_info = get_local_module_info(name)
    if module_info is not None:
        return module_info.directory
    else:
        return None
