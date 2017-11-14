# Tracking functions, independent of GUI go here


import numpy as np
import matplotlib.pyplot as plt
import motmot.FlyMovieFormat.FlyMovieFormat as FMF
from skimage.filters import threshold_otsu
from skimage.measure import label, regionprops
from skimage.morphology import binary_erosion

def convert_img_to_float(img):
    """Converts all pixels in an image to between 0. and 1. (inclusive).

    Parameters
    ----------
    img : np.array
        Image to convert.

    Returns
    -------
    img : np.array, dtype=np.float
        All pixels should be between 0 and 1.
    """
    img_as_float = img.copy().astype(np.float)
    img_as_float /= (np.max(img_as_float) * 1.)
    return img_as_float

def convert_img_to_uint8(img):
    """Converts all pixels in an image to between 0 and 255 (inclusive).

    Parameters
    ----------
    img : np.array
        Image to convert.

    Returns
    -------
    img : np.array, dtype=np.uint8
        All pixels should be between 0 and 255.
    """
    img = img.copy().astype(np.float)
    img /= (np.max(img) * 1.)
    img *= 255
    return img.astype(np.uint8)

def calc_background_image(vid, n_frames=200):
    """Caclculates a background image from a given video.

    Parameters
    ----------
    vid : motmot.FlyMovieFormat.FlyMovie
        Video to calculate background from.

    n_frames : int, optional (default=200)
        How many frames to use to calculate background.

    Returns
    -------
    background_image : np.array, dtype=np.uint8
        Background image
    """
    background_image = np.zeros(shape=(vid.get_height(), vid.get_width())).astype(np.float)
    random_ixs = np.random.randint(0, vid.get_n_frames() - 1, n_frames)

    for ix in random_ixs:
        background_image += vid.get_frame(ix)[0]

    background_image /= (n_frames * 1.)
    return background_image.astype(np.uint8)

def threshold_image(img, b_img, threshold=None):
    """Subtracts off background and thresholds current image.

    img : np.array, np.uint8
        Image to be thresholded.

    b_img : np.array, np.uint8
        Background image.

    threshold : float, optional (default=None)
        This should be within the range [0, 1]. If None,
        an otsu threshold will be calculated.

    Returns
    -------
    binary_image : np.array, np.float
        Pixels will be either 0 or 1.
    """
    # subtract off the background from the current image.
    sub_image = convert_img_to_float(img) - convert_img_to_float(b_img)
    # invert the image so that the region we are interested in has a
    # positive value.
    sub_image = -sub_image

    # only look at pixels with a value greater than the threshold (if specified)
    if threshold is None:
        threshold = threshold_otsu(sub_image)

    binary_image = np.zeros_like(sub_image)
    binary_image[np.where(sub_image > threshold)] = 1

    return binary_image

def find_mouse(img, b_img, threshold=None):
    """Finds a blob (a mouse) in the given image.

    Parameters
    ----------
    img : np.array
        Current image to find mouse within.

    b_img : np.array
        Background image to subtrack from current img.

    threshold : float, optional (default=None)

    Returns
    -------
    props : skimage.regionprops, or -1
        Properties of the detected mouse or -1 if we couldn't
        find a mouse.
    """
    mask = threshold_image(img, b_img, threshold)

    # Erode image to try and split up unrelated - possibly disconnected areas.
    eroded_img = binary_erosion(mask)

    labeled_image = label(eroded_img)
    props = regionprops(labeled_image)

    if len(props) == 0:
        return -1

    areas = []
    for prop in props:
        areas.append(prop.area)

    # return the region property with the largest area,
    # which we will assume to contain the mouse.
    largest_area_ix = np.argsort(areas)[-1]

    return props[largest_area_ix]

def track_video(vid, threshold=None, background_n_frames=200):
    """Tracks a passed video.

    Parameters
    ----------
    vid : motmot.FlyMovieFormat.FlyMovie
        Video to track.

    threshold : float, optional (default=None)
        Cutoff threshold. This specifies values to keep,
        contained in the current frame, following background
        subtraction.

    background_n_frames : int, optional (default=200)
        How many frames to use for background sub.

    Returns
    -------
    props : list of regionprops
        Region properties (which may or may not represent) the
        mouse, calculated for every frame of the video.
    """

    b_img = calc_background_image(vid, n_frames=background_n_frames)

    props = []
    for ix in xrange(vid.get_n_frames()):
        img, _ = vid.get_frame(ix)
        props.append(
            find_mouse(img, b_img, threshold=threshold)
            )

    return props
