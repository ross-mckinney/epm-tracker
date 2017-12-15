# Behavioral statistics

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.path as mpl_path
from scipy.spatial.distance import cdist, pdist, squareform


def get_per_frame_distance_traveled(tracking_data, conversion_factor=1.):
    """Gets the distance traveled between each successive frame contained in
    tracking_data.

    Parameters
    ----------
    tracking_data : TrackingData

    conversion_factor : float
        Number of pixels in 1 (unspecified) unit of distance. For example,
        if there are 100 pixels in 1 cm, pass "conversion_factor=100" to get
        the total distance traveled in cm.

    Returns
    -------
    total_distance_traveled : float
    """
    return np.sqrt(
        np.diff(tracking_data.rr)**2 + np.diff(tracking_data.cc)**2
        ) * (1./conversion_factor)

def get_total_distance_traveled(tracking_data, conversion_factor=1.):
    """Gets the total distance (possibly in converted units) traveled by a
    mouse in the EPM.

    Parameters
    ----------
    tracking_data : TrackingData

    conversion_factor : float
        Number of pixels in 1 (unspecified) unit of distance. For example,
        if there are 100 pixels in 1 cm, pass "conversion_factor=100" to get
        the total distance traveled in cm.

    Returns
    -------
    total_distance_traveled : float
    """
    return np.nansum(
        get_per_frame_distance_traveled(tracking_data, conversion_factor)
        )

def _get_time_in_arm(tracking_data, arena, arm):
    """Gets time in one set of arms present in the passed arena.

    Parameters
    ----------
    arm : string, options ("closed_arms", or "open_arms")
    """
    frames_in_arm = 0
    total_frames = tracking_data.rr.size

    for arm in getattr(arena, arm):
        polygon_path = mpl_path.Path(arena.arm_node_pairs[arm])
        for ix in xrange(total_frames):
            p = (tracking_data.rr[ix], tracking_data.cc[ix])
            if polygon_path.contains_point(p):
                frames_in_arm += 1

    return (frames_in_arm * 1.) / total_frames

def get_time_in_open_arms(tracking_data, arena):
    """Gets the fraction of time that a mouse spent in the open arms
    of the EPM.

    Parameters
    ----------
    tracking_data : TrackingData

    arena : EPMArena

    Returns
    -------
    time_in_open_arms : float
        Fraction of time that the mouse spent in the open arms of the EPM.
    """
    if arena.open_arms is None:
        raise AttributeError('EPMArena object "arena", must have its ' +
            '"open_arms" attribute set before this function can be called.')

    return _get_time_in_arm(tracking_data, arena, 'open_arms')

def get_time_in_closed_arms(tracking_data, arena):
    """Gets the fraction of time that a mouse spent in the closed arms
    of the EPM.

    Parameters
    ----------
    tracking_data : TrackingData

    arena : EPMArena

    Returns
    -------
    time_in_closed_arms : float
        Fraction of time that the mouse spent in the closed arms of the EPM."""
    if arena.closed_arms is None:
        raise AttributeError('EPMArena object "arena", must have its ' +
            '"closed_arms" attribute set before this function can be called.')

    return _get_time_in_arm(tracking_data, arena, 'closed_arms')

def get_time_in_center(tracking_data, arena):
    """Gets the fraction of time that a mouse spent in the center of the EPM.

    Parameters
    ----------
    tracking_data : TrackingData

    arena : EPMArena

    Returns
    -------
    time_in_center : float
        Fraction of time that the mouse spent in the center of the EPM."""
    frames_in_center = 0
    total_frames = tracking_data.rr.size

    polygon_path = mpl_path.Path(arena.central_nodes)
    for ix in xrange(total_frames):
        p = (tracking_data.rr[ix], tracking_data.cc[ix])
        if polygon_path.contains_point(p):
            frames_in_center += 1

    return (frames_in_center * 1.) / total_frames

def get_unidentified_frames(tracking_data, arena):
    """Gets the indeces of the frames where the mouse was found to be
    outside of each of the following: (1) the open arms, (2) the closed
    arms, and (3) the center of the EPM.

    This is mainly for troubleshooting.
    """
    unknown_ixs = []
    n_frames = tracking_data.rr.size

    paths = []
    for arm in arena.arm_node_pairs:
        paths.append(mpl_path.Path(arm))
    paths.append(mpl_path.Path(arena.central_nodes))

    for ix in xrange(n_frames):
        in_path = False
        p = (tracking_data.rr[ix], tracking_data.cc[ix])
        for path in paths:
            if path.contains_point(p):
                in_path = True
                break
        if not in_path:
            unknown_ixs.append(ix)
    return np.array(unknown_ixs)
