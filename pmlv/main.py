"""Entry point"""
import math
import os
import typing as tg
from pathlib import Path

from pmlv.args import process_args
import pmlv.ffmpeg as ffmpeg
from pmlv.html import read_toc, generate_html
from pmlv.ppt import wait_for_powerpoint


def doitall():
    args = process_args(ffmpeg.get_videoresolution)
    wait_for_powerpoint(args.inputfile)
    if not Path(args.outputdir).exists():
        os.mkdir(args.outputdir, mode=0o755)
    if hasattr(args, 'split_at'):
        print("Searching for split times: --split-at", args.split_at)
        splitlogofile = ffmpeg.make_pgm_logo(args.splitlogo, args.outputdir)
        splittimes = ffmpeg.find_rect(splitlogofile, args.splitlogoregion,
                                      args.inputfile,
                                      add_start_and_end=True)
        os.remove(splitlogofile)
        print("split times: ", splittimes)
        ffmpeg.encode_in_parts(args.inputfile, args.outputdir, splittimes)
    else:
        splittimes = [0.0, math.nan]
    numvideos = len(splittimes) - 1
    if hasattr(args, 'stop_at'):
        print("Searching for stops in %d video%s: --stop-at"%
              (numvideos, "s" if numvideos != 1 else ""), args.stop_at)
        stoplogofile = ffmpeg.make_pgm_logo(args.stoplogo, args.outputdir)
        stoptimes = ffmpeg.find_stops(numvideos, stoplogofile, args.stoplogoregion,
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
