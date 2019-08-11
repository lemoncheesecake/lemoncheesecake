'''
Created on Jan 1, 2017

@author: nicolas
'''

import os
import platform
import time
import glob
import re
import shutil

DEFAULT_REPORT_DIR_NAME = "report"


def archive_dirname_datetime(ts, archives_dir):
    return time.strftime("report-%Y%m%d-%H%M%S", time.localtime(ts))


# TODO: create two different functions
def report_dir_with_archiving(top_dir, archive_dirname_callback):
    archives_dir = os.path.join(top_dir, "reports")

    if platform.system() == "Windows":
        report_dir = os.path.join(top_dir, DEFAULT_REPORT_DIR_NAME)
        if os.path.exists(report_dir):
            if not os.path.exists(archives_dir):
                os.mkdir(archives_dir)
            os.rename(
                report_dir, os.path.join(archives_dir, archive_dirname_callback(os.path.getctime(report_dir), archives_dir))
            )
        os.mkdir(report_dir)

    else:
        if not os.path.exists(archives_dir):
            os.mkdir(archives_dir)

        report_dirname = archive_dirname_callback(time.time(), archives_dir)

        report_dir = os.path.join(archives_dir, report_dirname)
        os.mkdir(report_dir)

        symlink_path = os.path.join(os.path.dirname(report_dir), "..", DEFAULT_REPORT_DIR_NAME)
        if os.path.lexists(symlink_path):
            os.unlink(symlink_path)
        os.symlink(report_dir, symlink_path)

    return report_dir


def _list_directories_for_rotation(top_dir, dir_prefix):
    dirs = {}
    for dirname in glob.glob(os.path.join(top_dir, "%s*" % dir_prefix)):
        m = re.compile(r"^%s(\d+)$" % dir_prefix).search(os.path.basename(dirname))
        if m is not None:
            dirs[int(m.group(1))] = dirname
    return dirs


def _remove_obsolete_directories(directories, limit):
    if limit is None or len(list(filter(lambda num: num <= limit, directories.keys()))) < limit:
        return directories

    new_dirs = {}
    for dir_num, dir_path in directories.items():
        if dir_num >= limit:
            # directory could be a link if is has been previously created by report_dir_with_archiving:
            if os.path.islink(dir_path):
                os.remove(dir_path)
            else:
                shutil.rmtree(dir_path)
        else:
            new_dirs[dir_num] = dir_path
    return new_dirs


def _rotate_directory(num, dirname):
    next_num = num + 1
    next_dirname = re.sub(r"\d+$", str(next_num), dirname)
    if os.path.exists(next_dirname):
        _rotate_directory(next_num, next_dirname)
    os.rename(dirname, next_dirname)


def _rotate_directories(directories):
    if 1 in directories:
        _rotate_directory(1, directories[1])


def create_report_dir_with_rotation(top_dir, archiving_limit=20):
    report_dir = os.path.join(top_dir, DEFAULT_REPORT_DIR_NAME)
    if os.path.exists(report_dir):
        archiving_dir = os.path.join(top_dir, "reports")
        if not os.path.exists(archiving_dir):
            os.mkdir(archiving_dir)
        _rotate_directories(
            _remove_obsolete_directories(
                _list_directories_for_rotation(archiving_dir, "report-"), limit=archiving_limit
            )
        )
        os.rename(report_dir, os.path.join(archiving_dir, "report-1"))

    os.mkdir(report_dir)

    return report_dir
