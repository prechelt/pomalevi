"""Knows about command structure, argument parsing, defaults, and checks."""

import argparse
import re
import typing as tg
from pathlib import Path


description = "PowerPoint-based maintainable lecture videos tool"
projectsite = "https://github.com/prechelt/pomalevi"

def parse_args():
    #----- configure and use argparser:
    parser = argparse.ArgumentParser(
            description=description, epilog=projectsite)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='show the ffmpeg commands as they are run')
    parser.add_argument('--cssfile', type=str, metavar='path/mycss.css',
                        help='CSS file to be copied to outputdir')
    parser.add_argument('--cssurl', type=str, metavar='http://.../mycss.css or mycss.css',
                        help='relative or absolute URL to CSS')
    parser.add_argument('--split-at', type=str, metavar='ll:splitlogo.png',
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
    from pmlv.ffmpeg import imagesize
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


