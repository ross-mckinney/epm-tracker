# code for analyzing the tracks of mice in the EPM

import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.path as mpl_path
from scipy.spatial.distance import cdist, pdist, squareform

class TrackingData:
    """Object to read/store/handle tracking data in an .xlsx file."""
    COLUMN_NAMES = ['rr', 'cc', 'area', 'maj', 'min']
    def __init__(self, file_name):
        self.file_name = file_name
        self._df = pd.read_excel(file_name)
        self._setattr_from_df()

    def _setattr_from_df(self):
        """Sets class attributes from underlying _df data."""
        for attr in self.COLUMN_NAMES:
            setattr(self, attr, self._df[attr].values)

    def get_data_as_df(self):
        return self._df


class EPMArena:
    """Object to read/store/handle the EPM arena in which a mouse was
    tracked.

    Attributes
    ----------
    nodes : np.array of shape [12, 2]
        The positions of all of the points that define the EPM mask.
        This and all subsequent coordinate pairs are in pixel coordinates:
        ie. (rr, cc).

    center_of_mass : np.array of shape [2]
        The center of mass of all of the points that define the EPM mask.

    central_nodes : np.array of shape [4, 2]
        The positions of the four points that define the center of the
        EPM arena.

    exterior_nodes : np.array of shape [8, 2]
        The positions of the eight points that define the exterior edges of
        the EPM arena.

    exterior_node_pairs : np.array of shape [4, 2, 2]
        The positions of the eight points that define the exterior edges of the
        EPM arena. Here, each of the two points that define the edges of a
        single arm of the EPM arena are placed into a sub-matrix for easier
        access.

    arm_node_pairs : np.array of shape [4, 4, 2]
        The positions of the nodes that define each of the arms; these are not
        ordered in any particular manner.
    """
    COLUMN_NAMES = ['rr', 'cc']
    def __init__(self, file_name):
        self.file_name = file_name
        self._df = pd.read_excel(file_name)
        self.nodes = self._df.iloc[:, 1:].values
        self.center_of_mass = np.mean(self.nodes, axis=0)
        self.open_arms = None
        self.closed_arms = None

        self._set_central_and_exterior_nodes()
        self._set_exterior_node_pairs()
        self._set_arm_node_pairs()

    def _sort_points(self, points):
        """Sorts the given points in clockwise order.

        Parameters
        ----------
        points : np.array of shape [N, 2]

        Returns
        -------
        sorted_points : np.array of shape [N, 2]
        """
        center = np.mean(points, axis=0)
        rel_points = points - center
        angles = np.arctan2(rel_points[:, 0], rel_points[:, 1])
        sorted_rel_points = rel_points[np.argsort(angles)]
        sorted_points = sorted_rel_points + center
        return sorted_points

    def _set_central_and_exterior_nodes(self):
        """Sets the four central-most and 8 exterior-most points."""
        # calcuate the distance between the center of mass and
        # each of the nodes. Closest 4 are center.
        dists = cdist(self.nodes, np.array([self.center_of_mass]))
        ixs = np.argsort(dists[:, 0])
        self.central_nodes = self._sort_points(self.nodes[ixs[:4], :])
        self.exterior_nodes = self.nodes[ixs[4:], :]

    def _set_exterior_node_pairs(self):
        """Finds and sets pairs of exterior nodes that represent the edges of
        each arm of the EPM."""
        pair_ixs = []
        dists = squareform(pdist(self.exterior_nodes))
        for i in xrange(dists.shape[0]):
            ix = np.argsort(dists[i, :])[1]
            pix = [i, ix]
            pin = False
            for j in xrange(len(pair_ixs)):
                if set(pix) == set(pair_ixs[j]):
                    pin = True
            if not pin:
                pair_ixs.append([i, ix])
        ext_node_pairs = []
        for node_pair_ix in pair_ixs:
            ext_node_pairs.append(
                [self.exterior_nodes[node_pair_ix[0]],
                 self.exterior_nodes[node_pair_ix[-1]]]
                 )
        self.exterior_node_pairs = np.asarray(ext_node_pairs)

    def _set_arm_node_pairs(self):
        """Sets the four arms of the arms of the arena."""
        # find the midpoint of each of the pairs of external nodes.
        exterior_mids = []
        arms = []
        for i in xrange(self.exterior_node_pairs.shape[0]):
            exterior_nodes = self.exterior_node_pairs[i]
            exterior_mid = np.mean(exterior_nodes, axis=0)
            dists = cdist(self.central_nodes, np.array([exterior_mid]))
            ixs = np.argsort(dists[:, 0])[:2]
            arm = np.vstack((exterior_nodes, self.central_nodes[ixs,:]))
            arm = self._sort_points(arm)
            arms.append(arm.tolist())
        self.arm_node_pairs = np.array(arms)

    def get_central_nodes(self):
        return self.central_nodes

    def get_arm_node_pairs(self):
        return self.arm_node_pairs

    def plot_arms(self, ax=None):
        """Plots each of the arm segments, with its index label."""
        if ax is None:
            fig, ax = plt.subplots()

        for i in xrange(self.arm_node_pairs.shape[0]):
            arm_nodes = self.arm_node_pairs[i]
            ax.scatter(arm_nodes[:, 1], arm_nodes[:, 0],
                color='C{}'.format(i), alpha=0.5)
            # ax.scatter(arm_nodes[2:, 1], arm_nodes[2:, 0], color='k')
            arm_centroid = np.mean(arm_nodes, axis=0)
            ax.text(arm_centroid[1], arm_centroid[0], '{}'.format(i))

        ax.set_xlim(0, 320)
        ax.set_ylim(0, 240)
        ax.invert_yaxis()
        return ax

    def set_open_arms(self, *args):
        """Specify which of the EPM arms are 'open'.

        Parameters
        ----------
        *args : list of open arm indeces.
            The open arm indeces correspond the the position of each arm
            (its index) in this classes "arm_node_pairs" attribute. For a
            visual representation of the order that each of the arms is
            positioned in this array, call "plot_arms()".
        """
        self.open_arms = list(args)

    def set_closed_arms(self, *args):
        """Specify which of the EPM arms are 'closed'.

        Parameters
        ----------
        *args : list of open arm indeces.
            The open arm indeces correspond the the position of each arm
            (its index) in this classes "arm_node_pairs" attribute. For a
            visual representation of the order that each of the arms is
            positioned in this array, call "plot_arms()".
        """
        self.closed_arms = list(args)


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
    return np.sum(
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
