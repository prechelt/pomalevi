import os
import re
import shutil
import tempfile
import time

import pytest

def test_basic_functionality():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as mydir:
        pomdir = os.path.dirname(__file__) + "/.."  # one above 'test'
        #----- prepare files:
        shutil.copytree("test/testdata", mydir, dirs_exist_ok=True)
        shutil.copy("img/splitlogo.png", mydir)
        shutil.copy("img/stoplogo.png", mydir)
        #----- remember toc contents (must all be single-line):
        with open("test/testdata/mini-toc.txt", 'rt') as f:
            toc1_title = f.readline().rstrip()
            assert f.readline().rstrip() == ""
            toc1_p1 = f.readline().rstrip()
            assert f.readline().rstrip() == ""
            toc1_p2 = f.readline().rstrip()
        with open("test/testdata/mini-othertoc.txt", 'rt') as f:
            toc2_title = f.readline().rstrip()
            assert f.readline().rstrip() == ""
            toc2_p1 = f.readline().rstrip()
            assert f.readline().rstrip() == ""
            toc2_p2 = f.readline().rstrip()
        #----- run pomalevi with split and stop:
        os.chdir(mydir)  # we work in the scratch directory
        cmd = f"python {pomdir}/pomalevi.py mini.wmv"
        os.system(cmd)
        #----- check outputdir:
        assert os.path.exists("mini/index.html")
        assert os.path.exists("mini/favicon.png")
        assert os.path.exists("mini/pomalevi.css")
        assert os.path.exists("mini/v1.mp4")
        assert os.path.exists("mini/v2.mp4")
        assert not os.path.exists("mini/v3.mp4")
        with open("mini/index.html", 'rt') as f:
            html = f.read()
            # print(html)
            print("matching '%s'" % toc1_title)
            assert html.find(f"<title>{toc1_title}</title>") > 0
            print("matching '%s'" % toc1_p1)
            assert html.find(f"<td>{toc1_p1}</td>") > 0
            print("matching '%s'" % toc1_p2)
            assert html.find(f"<td>{toc1_p2}</td>") > 0
            stoptimes = "pmlv_stoptimes = [[3.53], []]"
            print("matching '%s'" % stoptimes)
            assert html.find(stoptimes) > 0
        v1_size = os.stat("mini/v1.mp4").st_size
        v2_size = os.stat("mini/v2.mp4").st_size
        assert 140000 < v1_size < 160000
        assert 85000 < v2_size < 90000
        #----- patch toc:
        #----- check new toc:
        #----- prepare cleanup on Windows:
        # Windows fails when removing the tempdir, because we are in it:
        os.chdir('..')
