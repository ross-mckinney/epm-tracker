import os
import shutil
import subprocess
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import motmot.FlyMovieFormat.FlyMovieFormat as FMF
import numpy as np


def fmf_ucmp(
    video_in,
    video_out,
    timestamps_in='None',
    fps=None,
    width=320,
    height=240):
    """Converts any file format to FlyMovieFormat.

    Parameters
    ----------
    video_in : string
        Path to compressed video.

    video_out : string
        Path to save uncompressed, .fmf video.

    timestamps_in : string or None (default = None)
        Path to .gz file containing timestamps for video.

    fps : int or None (default = None)
        Frame rate to save uncompressed video.

    width : int (optional, default=640)
        Width of video, in pixels.

    height : int (optional, default=480)
        Height of video, in pixels.
    """
    ts_file_given = os.path.isfile(timestamps_in)
    if ts_file_given:
        timestamps = np.loadtxt(timestamps_in)

    command = [
        'ffmpeg',
        '-i', video_in,
        '-f', 'image2pipe',
        '-pix_fmt', 'gray8',
        '-vf', 'scale=320:240',
        '-an',
        '-vcodec', 'rawvideo',
        '-'
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)

    vid = FMF.FlyMovieSaver(video_out)
    try:
        count = 0
        while True:
            raw_img = pipe.stdout.read(width*height)
            img = np.fromstring(raw_img, dtype=np.uint8)
            img = img.reshape((height, width))
            if ts_file_given:
                vid.add_frame(img, timestamps[count])
            else:
                vid.add_frame(img)
            count += 1
    except:
        pipe.stdout.close()
        pipe.wait()
        del pipe

    vid.close()
