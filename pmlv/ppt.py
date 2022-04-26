"""Knows how MS Powerpoint behaves and how PPTX files are structured."""
import os
import time


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