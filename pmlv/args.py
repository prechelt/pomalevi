"""Knows about command structure, argument parsing, defaults, and checks."""

import argparse
import os, os.path
import re
import typing as tg

import pmlv.base as base


description = "PowerPoint-based maintainable lecture videos tool"
projectsite = "https://github.com/prechelt/pomalevi"

def process_args(get_videoresolution: callable, get_imagesize: callable):
    #----- configure and use argparser:
    parser = argparse.ArgumentParser(
            description=description, epilog=projectsite)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='show the ffmpeg commands as they are run')
    parser.add_argument('--cssfile', type=str, metavar='path/mycss.css',
                        help='CSS file to be copied to outputdir')
    parser.add_argument('--cssurl', type=str, metavar='http://.../mycss.css or mycss.css',
                        help='relative or absolute URL to CSS')
    parser.add_argument('--format', type=str,
                        choices=["mp4q4", "mp4q3", "mp4q2", "mp4q1", "webm"], default="mp4q3",
                        help='default file type & quality: mp4q3')
    parser.add_argument('--out', type=str, dest="outputdir", metavar="outputdir",
                        help='directory to which output files will be written')
    parser.add_argument('--split-at', type=str, metavar='ll:splitlogo.png',
                        help='split when splitlogo appears in lower left corner (or lr, ul, ur)')
    parser.add_argument('--stop-at', type=str, metavar='ll:stoplogo.png',
                        help='stop when stoplogo appears in lower left corner (or lr, ul, ur)')
    parser.add_argument('--toc', type=str, metavar='inputfile-toc.txt',
                        help='content description: title, one paragraph per split part')
    parser.add_argument('inputfile', type=str,
                        help='video file to be processed (usually mp4 or wmv)')
    args = parser.parse_args()
    #----- determine helper args values:
    args.inputdir, args.inputfilename = os.path.split(args.inputfile)
    if not args.inputdir:
        args.inputdir = "."  # avoid creating paths like "/myslides" later
    args.inputbasename, args.inputsuffix = os.path.splitext(args.inputfilename)
    #----- promote -v globally:
    if args.verbose:
        base.verbose = True
    #----- manually check for further problems:
    if not os.path.exists(args.inputfile):
        parser.error(f"file {args.inputfile} must be readable")
    if args.cssfile and not os.path.exists(args.cssfile):
        parser.error(f"file {args.cssfile} must be readable")
    # we do not check that args.outputdir is a writable directory or nonexisting
    #----- retrieve video resolution:
    args.vidwidth, args.vidheight = get_videoresolution(args.inputfile)
    print(f"Video resolution: {args.vidwidth}x{args.vidheight}")
    #----- handle defaults:
    handle_out(parser, args)
    handle_split_at(parser, args, get_imagesize)
    handle_stop_at(parser, args, get_imagesize)
    handle_toc(parser, args)
    return args


def handle_out(parser: argparse.ArgumentParser, args: argparse.Namespace):
    if args.outputdir is None:
        args.outputdir = f"{args.inputdir}/{args.inputbasename}"


def handle_split_at(parser: argparse.ArgumentParser, args: argparse.Namespace,
                    get_imagesize: callable):
    args.split_at_by_default = not args.split_at
    if args.split_at_by_default:
        args.split_at = "ll:splitlogo.png"
    args.splitlogo, args.splitlogoregion = parse_logo_info(
            parser, args, args.split_at, "--split-at", args.split_at_by_default,
            get_imagesize)


def handle_stop_at(parser: argparse.ArgumentParser, args: argparse.Namespace,
                   get_imagesize: callable):
    args.stop_at_by_default = not args.stop_at
    if args.stop_at_by_default:
        args.stop_at = "ll:stoplogo.png"
    args.stoplogo, args.stoplogoregion = parse_logo_info(
            parser, args, args.stop_at, "--stop-at", args.stop_at_by_default,
            get_imagesize)


def handle_toc(parser: argparse.ArgumentParser, args: argparse.Namespace):
    #if hasattr(args, "toc"):
    if args.toc:
        return  # use given toc; else impute default:
    where_to_look = (args.inputdir, f"{args.inputdir}/toc")
    tocfilename = f"{args.inputbasename}-toc.txt"  # can be found in local dir!
    args.toc = base.find(where_to_look, tocfilename)  # empty string if not found
    if args.toc:
        print(f"Using {args.toc} for table of contents")
    else:
        print("No table of contents (toc) file found. Will generate trivial toc.")


def parse_logo_info(argparser: argparse.ArgumentParser, args: argparse.Namespace,
                    logoinfo: str, optname: str, by_default: bool,
                    get_imagesize: callable
                   ) -> tg.Tuple[str,dict]:
    """
    logoinfo is the value of option --split-at or --stop-at (optname).
    Checks logo exists and logoregion information is OK.
    Returns logo filename and find_rect search region coordinates.
    When using defaults and logo does not exist, return (None, None).
    """
    #----- ensure we have a colon and get left/right parts:
    mm_global = re.fullmatch(r"(.+):(.+)", logoinfo)
    if not mm_global:
        argparser.error(f"{optname} must have two parts separated by ':'")
        return
    logoregion = mm_global.group(1)
    logofile = mm_global.group(2)
    #----- ensure logofile:
    where_to_look = (args.inputdir, f"{args.inputdir}/..", f"{args.inputdir}/toc")
    logofile_as_found = base.find(where_to_look, logofile)
    if not logofile_as_found:
        if by_default:
            return (None, None)
        else:
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
    logowidth, logoheight = get_imagesize(logofile_as_found)
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
    return (logofile_as_found, region)


