

class TrackingSettings:
    """Class used to keep track of user-defined tracking settings.

    Parameters
    ----------
    threshold : int, optional (default=None)
        Threshold for detecting mouse after background subtraction.

    background_n_frames : int, optional (default=200)
        How many frames to use to calculate background image.

    inclusion_mask : np.array, optional (default=None)
        Which region of the image should be included in tracking.

    inclusion_mask_filename : string, optional (default=None)
        File that contains information about inclusion_mask.

    save_filename : string, optional (default=None)
        Where to save tracked video file.
    """

    def __init__(self, threshold=None, background_n_frames=200,
        inclusion_mask=None, inclusion_mask_filename=None, save_filename=None):
        self.threshold = threshold
        self.background_n_frames = background_n_frames
        self.inclusion_mask = inclusion_mask
        self.inclusion_mask_filename = inclusion_mask_filename
        self.save_filename = save_filename
