
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.path as mpl_path
from scipy.spatial.distance import cdist, pdist, squareform

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
