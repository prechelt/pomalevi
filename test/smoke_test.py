import os
import re
import shutil
import tempfile
import time

import pytest

def test_encode():
    with tempfile.TemporaryDirectory() as mypath:
        mydir = os.path.basename(mypath)
        print(f"tempdir: mypath={mypath} mydir={mydir}")
        pomdir = os.path.dirname(__file__) + "/.."  # one above 'test'
        #----- prepare files:
        shutil.copytree("test/testdata", mypath, dirs_exist_ok=True)
        shutil.copy("img/splitlogo.png", mypath)
        shutil.copy("img/stoplogo.png", mypath)
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
        # on Windows, working _in_ the tempdir leads to infinite recursion
        # upon cleanup on Python 3.10: https://github.com/python/cpython/issues/74168
        # So we work one level farther up:
        os.chdir(f"{mypath}/..")
        cmd = f"python {pomdir}/pmlv/main.py {mydir}/mini.wmv"
        os.system(cmd)
        #----- check outputdir:
        assert os.path.exists(f"{mydir}/mini/index.html")
        assert os.path.exists(f"{mydir}/mini/favicon.png")
        assert os.path.exists(f"{mydir}/mini/pomalevi.css")
        assert os.path.exists(f"{mydir}/mini/v1.mp4")
        assert os.path.exists(f"{mydir}/mini/v2.mp4")
        assert not os.path.exists(f"{mydir}/mini/v3.mp4")
        with open(f"{mydir}/mini/index.html", 'rt') as f:
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
        v1_size = os.stat(f"{mydir}/mini/v1.mp4").st_size
        v2_size = os.stat(f"{mydir}/mini/v2.mp4").st_size
        assert 125000 < v1_size < 145000
        assert 70000 < v2_size < 90000
        #----- patch toc:  will become a TODO
        #----- check new toc:  will become a TODO
