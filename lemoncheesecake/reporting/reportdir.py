'''
Created on Jan 1, 2017

@author: nicolas
'''

import os
import platform
import time

def archive_dirname_datetime(ts, archives_dir):
    return time.strftime("report-%Y%m%d-%H%M%S", time.localtime(ts))

# TODO: create two different functions
def report_dir_with_archiving(top_dir, archive_dirname_callback):
    archives_dir = os.path.join(top_dir, "reports")

    if platform.system() == "Windows":
        report_dir = os.path.join(top_dir, "report")
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

        symlink_path = os.path.join(os.path.dirname(report_dir), "..", "report")
        if os.path.lexists(symlink_path):
            os.unlink(symlink_path)
        os.symlink(report_dir, symlink_path)

    return report_dir
