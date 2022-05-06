"""
Knows how to call ffmpeg.
See also for instance
http://ffmpeg.org/documentation.html
http://trac.ffmpeg.org/wiki/FFprobeTips

"""

import copy
import math
import re
import subprocess
import sys
import typing as tg

import attrs 

import pmlv.base as base

ffmpeg_cmd = "static_ffmpeg"
ffprobe_cmd = "static_ffprobe"

@attrs.define
class Encoding:
    # mp4: https://trac.ffmpeg.org/wiki/Encode/AAC
    #      https://trac.ffmpeg.org/wiki/Encode/H.264
    # webm: http://ffmpeg.org/ffmpeg-all.html#libopus-1
    #       http://ffmpeg.org/ffmpeg-all.html#libvpx
    #       https://sites.google.com/a/webmproject.org/wiki/ffmpeg
    #       https://trac.ffmpeg.org/wiki/Encode/VP9
    #       https://mattgadient.com/x264-vs-x265-vs-vp8-vs-vp9-examples/
    suffix: str  # filename suffix
    flags_v: str  # ffmpeg video codec settings
    flags_a: str  # ffmpeg audio codec settings



_encodings = dict(
    mp4q4 = Encoding("mp4", 
            "-c:v libx264 -crf 22 -preset medium -tune stillimage", 
            "-c:a aac -b:a 64k -movflags +faststart"),
    mp4q3 = Encoding("mp4", 
            "-c:v libx264 -crf 26 -preset medium -tune stillimage", 
            "-c:a aac -b:a 56k -movflags +faststart"),
    mp4q2 = Encoding("mp4", 
            "-c:v libx264 -crf 30 -preset medium -tune stillimage", 
            "-c:a aac -b:a 48k -movflags +faststart"),
    mp4q1 = Encoding("mp4", 
            "-c:v libx264 -crf 34 -preset medium -tune stillimage", 
            "-c:a aac -b:a 40k -movflags +faststart"),
    webm = Encoding("webm",
            "-c:v libvpx -b:v 200k -quality good -speed 3",
            "-c:a libopus -b:a 32k -cutoff 8000"),
)


def get_encoding(name: str, flags_v: str = None, flags_a: str = None):
    enc = copy.copy(_encodings[name])
    if flags_v:
        enc.flags_v = flags_v
    if flags_a:
        enc.flags_a = flags_a
    return enc


def make_pgm_logo(logofile: str, outputdir: str) -> str:
    pgmfile = f"{outputdir}/logo.pgm"
    cmd = f"{ffmpeg_cmd} -y -i {logofile} {pgmfile}"
    ffx_run(cmd)
    return pgmfile


def get_imagesize(imgfile: str) -> tg.Tuple[int,int]:
    """Returns (width, height) of image in imgfile. TODO: simplify!"""
    cmd = f"{ffprobe_cmd} -i {imgfile}"
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


def get_videoresolution(file: str) -> tuple[int, int]:
    """Return (width, height) in pixels. http://trac.ffmpeg.org/wiki/FFprobeTips#WidthxHeightresolution"""
    opts = "-v error -select_streams v:0 -show_entries stream=width,height -of csv=nk=0:p=0"
    output = ffx_getoutput(f"{ffprobe_cmd} -i {file} {opts}")
    mm = re.search(r"width=(\d+)", output)
    width = int(mm.group(1))
    mm = re.search(r"height=(\d+)", output)
    height = int(mm.group(1))
    return (width, height)


def get_videoduration_secs(file: str) -> float:
    """See http://trac.ffmpeg.org/wiki/FFprobeTips#Duration"""
    opts = "-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1"
    output = ffx_getoutput(f"{ffprobe_cmd} -i {file} {opts}")
    return float(output)


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
        Prints status every few video seconds.
        """
        result = [0.0] if add_start_and_end else []
        previous_quintasec = -1
        previous_is_match = False
        f = ['frame', '0.0']
        for line in file:
            # print(line)
            f = line.split(',')
            assert f[0] == "frame"
            quintasec = math.floor(float(f[1])/5.0) if f[1] else previous_quintasec
            if quintasec > previous_quintasec:
                previous_quintasec = quintasec
                print("%d secs processed, logo matched %dx" %
                      (5*quintasec, len(result) - add_start_and_end), end='\r')
            is_match = len(f) > 2  # frame,time,xcoord,ycoord
            if is_match and not previous_is_match:  # start of new match
                # print("\n", line[:-1])
                result.append(round(float(f[1]), 2))
            previous_is_match = is_match
        end = float(f[1])
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
    show_spec = "frame=pts_time:frame_tags=lavfi.rect.x,lavfi.rect.y"
    cmd = (f"{ffprobe_cmd} -f lavfi movie=%s,%s:%s -show_entries %s -of csv" %
           (inputfile, find_rect_filter, rectangle, show_spec))
    p = ffx_popen(cmd)
    result = newmatch_times(p.stdout, region)
    p.wait()  # wait for process to finish
    return result


def encode_in_parts(inputfile: str, encoding: Encoding,
                    outputdir: str, splittimes: tg.List[float]):
    n = len(splittimes) - 1  # start does not count
    print("Encoding %d video part%s" % (n, "s" if n != 1 else ""))
    for i in range(1, n+1):  # i in 1..n for building v{i}.*
        from_to = f"-ss %.2f -to %.2f" % (splittimes[i-1], splittimes[i])
        outputfile = f"{outputdir}/v{i}.{encoding.suffix}"
        cmd = (f"{ffmpeg_cmd} -y {from_to} -i {inputfile} "
               f"{encoding.flags_v} {encoding.flags_a} {outputfile}")
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
                    mm = re.search("time=.+speed=[\d\.]+x", part)
                    if mm:
                        print(mm.group(0), end='\r')
            remainder = parts[-1]  # if this happens to be a complete line: bad luck!
    print("Encoding DONE")


def find_stops(numvideos: int, suffix: str, stoplogo: str, region: dict,
               outputdir: str) -> base.Stoptimes:
    result = []
    for i in range(1, numvideos+1):  # i in 1..numvideos for scanning v{i}.*
        videofile = f"{outputdir}/v{i}.{suffix}"
        stoptimes = find_rect(stoplogo, region, videofile) 
        result.append(stoptimes)
    return result


def ffx_getoutput(cmd: str) -> str:
    base.trace(cmd)
    status, output = subprocess.getstatusoutput(cmd)
    if status != 0:
        print(f"Command ''{cmd}'' failed!  {output}")  # will 'resolve' itself somehow...
        sys.exit(1)
    return output


def ffx_popen(cmd: str, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
             ) -> subprocess.Popen:
    """
    Popen ffmpeg cmd with stdout and stderr as given; at most one of them a pipe.
    Caller must read the pipe to the end and then call p.wait().
    """
    base.trace(cmd)
    LINEBUFFERED = 1
    return subprocess.Popen(cmd,
        bufsize=LINEBUFFERED, stdout=stdout, stderr=stderr,
        shell=True, encoding='utf8', text=True)


def ffx_run(cmd: str) -> subprocess.CompletedProcess:
    """Run ffmpeg cmd with output suppressed."""
    base.trace(cmd)
    return subprocess.run(cmd, capture_output=True, check=True, shell=True)
