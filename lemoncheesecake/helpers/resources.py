import os.path as osp


def get_resource_path(relpath):
    if isinstance(relpath, (list, tuple)):
        relpath = osp.join(*relpath)

    return osp.join(osp.dirname(__file__), osp.pardir, "resources", relpath)
