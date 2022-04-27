"""
Knows how to call ffmpeg.
See also for instance
http://ffmpeg.org/documentation.html
http://trac.ffmpeg.org/wiki/FFprobeTips

"""

import math
import re
import subprocess
import typing as tg

from pmlv.base import Stoptimes

ffmpeg_cmd = "ffmpeg"
ffprobe_cmd = "ffprobe"

def make_pgm_logo(logofile: str, outputdir: str) -> str:
    pgmfile = f"{outputdir}/logo.pgm"
    cmd = f"ffmpeg -y -i {logofile} {pgmfile}"
    ffx_run(cmd)
    return pgmfile


def get_videoresolution(file: str) -> tuple[int, int]:
    """Return (width, height) in pixels. http://trac.ffmpeg.org/wiki/FFprobeTips#WidthxHeightresolution"""
    opts = "-v error -select_streams v:0 -show_entries stream=width,height -of csv=nk=0:p=0"
    output = ffx_getoutput(f"{ffprobe_cmd} -i {file} {opts}")
    mm = re.search(r"width=(\d+)", output)
    width = mm.group(1)
    mm = re.search(r"height=(\d+)", output)
    height = mm.group(1)
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


def ffx_getoutput(cmd: str) -> str:
    status, output = subprocess.getstatusoutput(cmd)
    if status != 0:
        print(f"Command ''{cmd}'' failed!")  # will 'resolve' itself somehow...
    return output


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
    print("##: ", msg)
