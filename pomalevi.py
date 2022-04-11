#!/usr/bin/env python3

import argparse
import datetime as dt
import math
import os
import time
from pathlib import Path
import re
import shutil
import subprocess
import typing as tg

description = "PowerPoint-based maintainable lecture videos tool"
projectsite = "https://github.com/prechelt/pomalevi"

Stoptimes = tg.List[tg.List[float]]

verbose = False  # global value for -v flag, set in parse_args()

def doitall():
    args = parse_args()
    if args.wait:
        wait_for_powerpoint(args.inputfile)
    if not Path(args.outputdir).exists():
        os.mkdir(args.outputdir, mode=0o755)
    if hasattr(args, 'split_at'):
        print("Searching for split times: --split-at", args.split_at)
        splitlogofile = make_pgm_logo(args.splitlogo, args.outputdir)
        splittimes = find_rect(splitlogofile, args.splitlogoregion,
                               args.inputfile, 
                               add_start_and_end=True)
        os.remove(splitlogofile)
        print("split times: ", splittimes)
        encode_in_parts(args.inputfile, args.outputdir, splittimes)
    else:
        splittimes = [0.0, math.nan]
    numvideos = len(splittimes) - 1
    if hasattr(args, 'stop_at'):
        print("Searching for stops in %d video%s: --stop-at"%
              (numvideos, "s" if numvideos != 1 else ""), args.stop_at)
        stoplogofile = make_pgm_logo(args.stoplogo, args.outputdir)
        stoptimes = find_stops(numvideos, stoplogofile, args.stoplogoregion,
                               args.outputdir)
        print("stop times: ", stoptimes)
        os.remove(stoplogofile)
    else:
        stoptimes = [[] for _ in range(numvideos)]
    if args.toc:
        title, toc = read_toc(args.toc, numvideos)
    else:
        basename = os.path.splitext(os.path.basename(args.inputfile))[0]
        title, toc = (basename, [f"part {i+1}" for i in range(numvideos)])
    generate_html(title, args.cssfile, args.cssurl, stoptimes, toc, args.outputdir)
    print("DONE.")


def parse_args():
    #----- configure and use argparser:
    parser = argparse.ArgumentParser(
            description=description, epilog=projectsite)
    parser.add_argument('--wait', action='store_true',
                        help='wait for inputfile export to finish (filesize change)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='show the ffmpeg commands as they are run')
    parser.add_argument('--cssfile', type=str, metavar='path/mycss.css',
                        help='CSS file to be copied to outputdir')
    parser.add_argument('--cssurl', type=str, metavar='http://.../mycss.css or mycss.css',
                        help='relative or absolute URL to CSS')
    parser.add_argument('--split-at', type=str, metavar='ur:splitlogo.png',
                        help='split when splitlogo appears in upper right corner (or ul, lr, ll)')
    parser.add_argument('--stop-at', type=str, metavar='ur:stoplogo.png',
                        help='stop when stoplogo appears in upper right corner (or ul, lr, ll)')
    parser.add_argument('--toc', type=str, metavar='contents.txt',
                        help='content description: title, one paragraph per split part')
    parser.add_argument('inputfile', type=str,
                        help='video file to be processed (usually mp4 or wmv)')
    parser.add_argument('outputdir', type=str,
                        help='directory to which output files will be written')
    args = parser.parse_args()
    global verbose
    verbose = args.verbose
    args.vidwidth = 1920  # hardcoded video size: FullHD
    args.vidheight = 1080
    #----- manually check for further problems:
    if not Path(args.inputfile).exists():
        parser.error(f"file {args.inputfile} must be readable")
    if args.cssfile and not Path(args.cssfile).exists():
        parser.error(f"file {args.cssfile} must be readable")
    # we do not check that args.outputdir is a writable directory or nonexisting
    if args.split_at:
        args.splitlogo, args.splitlogoregion = parse_logo_info(
                parser, args, args.split_at, "--split-at")
    if args.stop_at:
        args.stoplogo, args.stoplogoregion = parse_logo_info(
                parser, args, args.stop_at, "--stop-at")
    return args


def parse_logo_info(argparser: argparse.ArgumentParser, args: argparse.Namespace,
                    logoinfo: str, optname: str,
                   ) -> tg.Tuple[str,dict]:
    """
    logoinfo is the value of option --split-at or --stop-at (optname).
    Checks logo exists and logoregion information is OK.
    Returns logo filename and find_rect search region coordinates.
    """
    #----- ensure we have a colon and get left/right parts:
    mm_global = re.fullmatch(r"(.+):(.+)", logoinfo)
    if not mm_global:
        argparser.error(f"{optname} must have two parts separated by ':'")
        return
    logoregion = mm_global.group(1)
    logofile = mm_global.group(2)
    #----- ensure logofile:
    if not Path(logofile).exists():
        argparser.error(f"file {logofile} not found")
        return
    if not logofile.endswith(".png") and not logofile.endswith(".PNG"):
        argparser.error(f"{logofile} has wrong file type; must be *.png or *.PNG")
        return
    #----- parse logoregion:
    logoregion_regexp = r"ul|ur|ll|lr|x=(\d+)\.\.\.?(\d+),y=(\d+)\.\.\.?(\d+)"
    # e.g. x=0..100,y=900...1000
    mm_logoregion = re.fullmatch(logoregion_regexp, logoregion)
    if not mm_logoregion:
        argparser.error(f"{optname} left part must be ul, ur, ll, lr, or x=xmin..xmax,y=ymin..ymax")
        return
    #----- handle explicit logoregion and return:
    if mm_logoregion.lastindex:  # is None or 4
        mm = mm_logoregion
        region = dict(xmin=int(mm.group(1)), xmax=int(mm.group(2)), 
                      ymin=int(mm.group(3)), ymax=int(mm.group(4)))
        return (logofile, region)
    #----- compute region from ul, ur, ll, lr:
    logowidth, logoheight = imagesize(logofile)
    width_tol, height_tol = (int(logowidth/2), int(logoheight/2))  # search tolerance
    region = dict()
    if logoregion[0] == 'u':  # upper
        region['ymin'] = 0
        region['ymax'] = height_tol
    else:                  # lower
        region['ymin'] = args.vidheight - logoheight - height_tol - 1
        region['ymax'] = args.vidheight - logoheight - 1
    if logoregion[1] == 'l':  # left
        region['xmin'] = 0
        region['xmax'] = width_tol
    else:                  # right
        region['xmin'] = args.vidwidth - logowidth - width_tol - 1
        region['xmax'] = args.vidwidth - logowidth - 1
    assert set(region.keys()) == {'xmin', 'xmax', 'ymin', 'ymax'}
    return (logofile, region)


def wait_for_powerpoint(videofile: str):
    new_size = os.path.getsize(videofile)
    print("waiting for filesize of '%s' to change" % videofile)
    while True:
        time.sleep(5.0)
        old_size = new_size
        new_size = os.path.getsize(videofile)
        if new_size != old_size:
            break  # Powerpoint is finishing exporting: filesize has changed!
    print("waiting for filesize of '%s' to stop changing" % videofile)
    while True:
        # if the file comes from a different drive, it may take a while to arrive
        time.sleep(5.0)
        old_size = new_size
        new_size = os.path.getsize(videofile)
        if new_size == old_size:
            break  # Powerpoint is done: filesize has not changed!


def make_pgm_logo(logofile: str, outputdir: str) -> str:
    pgmfile = f"{outputdir}/logo.pgm"
    cmd = f"ffmpeg -y -i {logofile} {pgmfile}"
    ffx_run(cmd)
    return pgmfile


def find_rect(logopgmfile: str, region: dict, inputfile: str,
              add_start_and_end=False) -> tg.List[float]:
    """
    Use ffprobe to call the find_rect filter to find the frames in which
    the contents of logofile appear, with its upper left corner
    in region.
    For find_rect params, see https://trac.ffmpeg.org/ticket/8766.
    Returns the timestamp (in seconds) of the first frame of each stretch of such frames.
    """
    def newmatch_times(file, region: dict) -> tg.List[float]:
        """
        Returns the times at which stretches of matches start.
        Prints status once per minute.
        """
        result = [0.0] if add_start_and_end else []
        previous_quintasec = -1
        previous_is_match = False
        for line in file:
            fields = line.split(',')
            assert fields[0] == "frame"
            quintasec = math.floor(float(fields[1])/5.0)
            if quintasec > previous_quintasec:
                previous_quintasec = quintasec
                print("%d secs processed, logo matched %dx" %
                      (5*quintasec, len(result) - add_start_and_end), end='\r')
            is_match = len(fields) > 2  # frame,time,xcoord,ycoord
            if is_match and not previous_is_match:  # start of new match
                # print("\n", line[:-1])
                result.append(round(float(fields[1]), 2))
            previous_is_match = is_match
        end = float(fields[1])
        if add_start_and_end:
            if end - result[-1] > 2.0:
                result.append(end)
            else:  # avoid super-short final videos, which are probably a user mistake
                result[-1] = end  # overwrite near-the-end-split with end
        print("")  # leave progress line
        return result
    find_rect_filter = f"find_rect={logopgmfile}:threshold=0.2"
    r = region  # abbrev
    rectangle = f"xmin={r['xmin']}:xmax={r['xmax']}:ymin={r['ymin']}:ymax={r['ymax']}"
    show_spec = "frame=pkt_pts_time:frame_tags=lavfi.rect.x,lavfi.rect.y"
    cmd = ("ffprobe -f lavfi movie=%s,%s:%s -show_entries %s -of csv" %
           (inputfile, find_rect_filter, rectangle, show_spec))
    p = ffx_popen(cmd)
    result = newmatch_times(p.stdout, region)
    p.wait()  # wait for process to finish
    return result


def encode_in_parts(inputfile: str, outputdir: str, splittimes: tg.List[float]):
    n = len(splittimes) - 1  # start does not count
    print("Encoding %d video part%s" % (n, "s" if n != 1 else ""))
    # AAC params: https://trac.ffmpeg.org/wiki/Encode/AAC
    audio_args = "-c:a aac -b:a 64k -movflags +faststart"
    # H.264 params: https://trac.ffmpeg.org/wiki/Encode/H.264
    video_args = "-c:v libx264 -crf 23 -preset medium -tune stillimage"
    for i in range(1, n+1):  # i in 1..n for building v{i].mp4
        from_to = f"-ss %.2f -to %.2f" % (splittimes[i-1], splittimes[i])
        outputfile = f"{outputdir}/v{i}.mp4"
        cmd = (f"ffmpeg -y {from_to} -i {inputfile} "
               f"{video_args} {audio_args} {outputfile}")
        # os.system(cmd)
        p = ffx_popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        remainder = ""
        while True:  # produce progress output
            # ffmpegs progress indicator lines are terminated with \r, not \n,
            # so we have to do line splitting ourselves: 
            block = p.stderr.read(100)
            if not block:  # EOF
                print("", end='\n')
                break
            parts = block.splitlines()
            parts[0] = f"{remainder}{parts[0]}"
            for part in parts[:-1]:
                if part.startswith("frame="):  # a progress indicator line
                    pos = part.find("time=")
                    print(part[pos:], end='\r')  # the full line is rather long
            remainder = parts[-1]  # if this happens to be a complete line: bad luck!
    print("Encoding DONE")


def find_stops(numvideos: int, stoplogo: str, region: dict,
               outputdir: str) -> Stoptimes:
    result = []
    for i in range(1, numvideos+1):  # i in 1..numvideos for scanning v{i].mp4
        videofile = f"{outputdir}/v{i}.mp4"
        stoptimes = find_rect(stoplogo, region, videofile) 
        result.append(stoptimes)
    return result


def read_toc(tocfile: str, numvideos: int) -> tg.Tuple[str, tg.List[str]]:
    with open(tocfile, 'rt') as f:
        all = f.read()
    items = all.split('\n\n')
    title, items = items[0], items[1:]
    if len(items) < numvideos:
        items.extend((numvideos - len(items)) * [''])  # add items if too few
    return title, items[:numvideos]


html_template = """
<!DOCTYPE html>
<html>
  <head>
    <title>%(title)s</title>
    %(css_block)s
    <link rel="icon" type="image/png" href="%(favicon)s">
    <meta charset="UTF-8">
  </head>
  <body>

    <h1 class="pmlv-title">%(title)s</h1>

    <video id="pomalevi-video" class="pmlv-video"
           height=540 controls
           data-setup='{ "playbackRates": [0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.4, 1.7, 2.0] }'>>
       <!-- source src="v1.mp4" type="video/mp4" -->
       Your browser does not support the video tag.
    </video>

    <br>
    <button class="pmlv-button" onclick="pmlv_skip(pmlv_video, -10)">-10s</button>
    <button class="pmlv-button" onclick="pmlv_skip(pmlv_video, 10)">+10s</button>
    --
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 0.6)">0.6x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 0.7)">0.7x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 0.85)">0.85x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 1.0)">1.0x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 1.2)">1.2x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 1.4)">1.4x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 1.7)">1.7x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 2.0)">2.0x</button>

    <table class="pmlv-table">
      %(toc_rows)s
    </table>

    <footer class="pmlv-footer">
      <p>Generated %(date)s 
         by <a href="https://github.com/prechelt/pomalevi">pomalevi</a>:
         crude, but effective.
      </p>
    </footer>

    %(script)s

  </body>

</html>
"""

script_template = """
    <script>
      var pmlv_video = document.getElementById("pomalevi-video")
      var pmlv_video_idx = 1
      var pmlv_stoptimes = %(stoptimes)s  // list of list of floats: stop times in seconds

      function pmlv_pause_at_stoptimes() {
          for (var t of pmlv_stoptimes[pmlv_video_idx-1]) {
            if(pmlv_video.currentTime >= t && pmlv_video.currentTime <= t+0.6) {
              // 0.6s suffices even for Firefox at 2.0x speed. 0.5s does not.
              pmlv_video.pause()
              pmlv_video.currentTime += 0.6
            }
          }
      }

      function pmlv_skip(obj, secs) {
        obj.currentTime += secs
      }

      function pmlv_speed(obj, factor) {
        obj.playbackRate = factor
      }

      function pmlv_switch_to(i, play=true) {
        pmlv_video.src = "v" + i + ".mp4"
        pmlv_video_idx = i  // select the relevant stoptimes
        pmlv_video.load()
        if (play) {
          pmlv_video.play()
        }
      }

      pmlv_video.addEventListener("timeupdate", pmlv_pause_at_stoptimes)
      pmlv_switch_to(1, false)

    </script>
"""

def generate_html(title: str, 
                  cssfile: tg.Optional[str], cssurl: tg.Optional[str],
                  stoptimes: Stoptimes, 
                  toc: tg.List[str], outputdir: str):
    # https://html.spec.whatwg.org/multipage/media.html
    filename = f"{outputdir}/v.html"
    print(f"Generating {filename}")
    favicon_srcfile = f"{os.path.dirname(__file__)}/img/favicon.png"
    favicon_href = "favicon.png"
    date = dt.datetime.now().strftime("%Y-%m-%d")
    #----- prepare CSS block:
    if cssfile is None and cssurl is None:  # copy pomalevi default CSS
        css_srcfile = "%s/css/pomalevi.css" % os.path.dirname(__file__)
        css_href = "pomalevi.css"
    elif cssfile:  # copy given file
        css_srcfile = cssfile
        css_href = os.path.basename(cssfile)
    elif cssurl:
        css_srcfile = None
        css_href = cssurl
    css_block = f'    <link rel="stylesheet" href="{css_href}">'
    #----- prepare TOC:
    toc_rows = ""
    script = script_template % dict(stoptimes=stoptimes)
    for i in range(1, len(stoptimes)+1):
        as_link = f"onclick='pmlv_switch_to({i})'"
        num_cell = f"{i}"
        toc_cell = toc[i-1]
        toc_row = (f"\n      <tr class='pmlv-tablerow' {as_link}>"
                   f"<td class='pmlv-numcell'>{num_cell}</td>"
                   f"<td>{toc_cell}</td></tr>")
        toc_rows += toc_row
    #----- generate HTML:
    html = html_template % dict(title=title, 
                                favicon=favicon_href, 
                                css_block=css_block, 
                                toc_rows=toc_rows, date=date, script=script)
    #----- fill outputdir:
    with open(filename, 'wt', encoding='utf8') as f:
        f.write(html)
    shutil.copyfile(favicon_srcfile, f"{outputdir}/{favicon_href}")
    if css_srcfile:
        shutil.copyfile(css_srcfile, f"{outputdir}/{css_href}")


########## helpers:

def ffx_popen(cmd: str, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
             ) -> subprocess.Popen:
    """
    Popen ffmpeg cmd with stdout and stderr as given; at most one of them a pipe.
    Caller must read the pipe to end and then call p.wait().
    """
    trace(cmd)
    LINEBUFFERED = 1
    return subprocess.Popen(cmd,
        bufsize=LINEBUFFERED, stdout=stdout, stderr=stderr,
        shell=True, encoding='utf8', text=True)


def ffx_run(cmd: str) -> subprocess.CompletedProcess:
    """Run ffmpeg cmd with output suppressed."""
    trace(cmd)
    return subprocess.run(cmd, capture_output=True, check=True, shell=True)


def imagesize(imgfile: str) -> tg.Tuple[int,int]:
    """Returns (width, height) of image in imgfile."""
    cmd = f"ffprobe -i {imgfile}"
    p = ffx_popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for line in p.stderr:
        pass  # keep only the last line
    p.wait()
    # p prints a final line such as these:
    #     Stream #0:0: Video: pgm, gray, 122x105, 25 tbr, 25 tbn, 25 tbc
    #     Stream #0:0: Video: png, rgba(pc), 122x105 [SAR 4724:4724 DAR 122:105], 25 tbr, 25 tbn, 25 tbc
    # so we look for '123x456'-like things:
    pattern = r"(\d+)x(\d+)"
    mm = re.search(pattern, line)
    if mm:
        return (int(mm.group(1)), int(mm.group(2)))
    else:
        print(f"Cannot parse output of '{cmd}':\n", line)


def trace(msg: str):
    if verbose:
        print("##: ", msg)
 
 
if __name__ == '__main__':
    doitall()