import os.path as osp
import glob
import re

from lemoncheesecake.reporting.reportdir import create_report_dir_with_rotation


def prepare_report_dirs(top_dir, has_current=False, archive_nums=None):
    if has_current:
        top_dir.join("report").mkdir()

    if archive_nums is not None:
        top_dir.join("reports").mkdir()
        for num in archive_nums:
            top_dir.join("reports").mkdir("report-%d" % num)


def get_report_nums_in_dir(top_dir):
    for dirname in glob.glob(osp.join(top_dir, "report-*")):
        m = re.compile(r"report-(\d+)$").search(dirname)
        if m is not None:
            yield int(m.group(1))


def check_report_dirs(top_dir, has_current=False, archive_nums=None):
    assert osp.exists(top_dir.join("report").strpath) == has_current

    if archive_nums is not None:
        assert osp.exists(top_dir.join("reports").strpath)
        assert sorted(get_report_nums_in_dir(top_dir.join("reports").strpath)) == sorted(archive_nums)
    else:
        assert not osp.exists(top_dir.join("reports").strpath)


def test_first_report(tmpdir):
    path = create_report_dir_with_rotation(tmpdir.strpath)
    assert osp.exists(path)
    check_report_dirs(tmpdir, has_current=True, archive_nums=None)


def test_first_archiving(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True)
    create_report_dir_with_rotation(tmpdir.strpath)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1])


def test_first_rotation(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True, archive_nums=[1])
    create_report_dir_with_rotation(tmpdir.strpath)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2])


def test_first_removal(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2])
    create_report_dir_with_rotation(tmpdir.strpath, archiving_limit=2)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2])


def test_no_archiving_limit(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2])
    create_report_dir_with_rotation(tmpdir.strpath, archiving_limit=None)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2, 3])


def test_report_1_missing(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True, archive_nums=[2, 3])
    create_report_dir_with_rotation(tmpdir.strpath)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2, 3])


def test_report_2_missing(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True, archive_nums=[1, 3])
    create_report_dir_with_rotation(tmpdir.strpath)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2, 3])


def test_report_1_and_2_missing(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True, archive_nums=[3])
    create_report_dir_with_rotation(tmpdir.strpath)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1, 3])


def test_report_num_slots_free_1(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True, archive_nums=[2, 3])
    create_report_dir_with_rotation(tmpdir.strpath, archiving_limit=3)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2, 3])


def test_report_num_slots_free_2(tmpdir):
    prepare_report_dirs(tmpdir, has_current=True, archive_nums=[1, 3, 4])
    create_report_dir_with_rotation(tmpdir.strpath, archiving_limit=3)
    check_report_dirs(tmpdir, has_current=True, archive_nums=[1, 2, 3, 4])
