
import pandas as pd

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
