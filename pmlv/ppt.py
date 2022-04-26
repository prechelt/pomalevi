"""Knows how MS Powerpoint behaves and how PPTX files are structured."""
import os
import time


def wait_for_powerpoint(videofile: str):
    """
    While Powerpoint exports a video file, the file exists but has zero size.
    Only once the export is complete will the contents be copied to the target.
    """
    new_size = os.path.getsize(videofile)  # will be zero during export
    if new_size > 0:
        return  # assume the file is ready and no waiting is needed
        # risky if we get started near the end of the exporting
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