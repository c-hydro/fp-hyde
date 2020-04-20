# ----------------------------------------------------------------------------------------------------------------------
# Library
import os
import numpy as np
import glob
import re

# from ascat.read_native.cdr import AscatSsmCdr
from ascat.read_native.bufr import AscatL2SsmBufrChunked
from ascat.read_native.cdr import AscatNc

from pygeogrids.grids import CellGrid
from pynetcf.time_series import IndexedRaggedTs, GriddedNcTs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to interface ascat h16 swath files
class AscatDriverH16(AscatL2SsmBufrChunked):
    """
    Parameters
    ----------
    path: string
        path where the data is stored
    month_path_str: string, optional
        if the files are stored in folders by month as is the standard on
        the H SAF FTP Server then please specify the string that should be
        used in datetime.datetime.strftime
        Default: 'h16_%Y%m_buf'
    """

    def __init__(self, path,
                 file_search_str='h16_{datetime}*.buf',
                 month_path_str='h16_%Y%m_buf', chunk_minutes=50):

        day_search_str = 'h16_%Y%m%d_*.buf'
        datetime_format = '%Y%m%d_%H%M%S'
        filename_datetime_format = (4, 19, '%Y%m%d_%H%M%S')

        super(AscatDriverH16, self).__init__(path,
                                             month_path_str=month_path_str,
                                             day_search_str=day_search_str,
                                             file_search_str=file_search_str,
                                             datetime_format=datetime_format,
                                             filename_datetime_format=filename_datetime_format,
                                             chunk_minutes=chunk_minutes)


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to interface ascat h101 swath files
class AscatDriverH101(AscatL2SsmBufrChunked):
    """
    Parameters
    ----------
    path: string
        path where the data is stored
    month_path_str: string, optional
        if the files are stored in folders by month as is the standard on
        the H SAF FTP Server then please specify the string that should be
        used in datetime.datetime.strftime
        Default: 'h101_%Y%m_buf'
    """

    def __init__(self, path,
                 file_search_str='h101_{datetime}*.buf',
                 month_path_str='h101_%Y%m_buf',
                 chunk_minutes=50):

        day_search_str = 'h101_%Y%m%d_*.buf'
        datetime_format = '%Y%m%d_%H%M%S'
        filename_datetime_format = (5, 20, '%Y%m%d_%H%M%S')

        super(AscatDriverH101, self).__init__(path,
                                              month_path_str=month_path_str,
                                              day_search_str=day_search_str,
                                              file_search_str=file_search_str,
                                              datetime_format=datetime_format,
                                              filename_datetime_format=filename_datetime_format,
                                              chunk_minutes=chunk_minutes)

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to interface ascat data record files
class AscatDriverSsmCdr(AscatNc):

    """
    Class reading Metop ASCAT soil moisture Climate Data Record (CDR).

    Parameters
    ----------
    cdr_path : str
        Path to Climate Data Record (CDR) data set.
    grid_path : str
        Path to grid file.
    grid_filename : str
        Name of grid file.
    static_layer_path : str
        Path to static layer files.

    Attributes
    ----------
    grid : pygeogrids.CellGrid
        Cell grid.
    """

    def __init__(self, cdr_path, grid_path, cdr_tmpl_filename=None,
                 grid_filename='TUW_WARP5_grid_info_2_2.nc',
                 static_layer_path=None, **kwargs):

        first_file = glob.glob(os.path.join(cdr_path, '*.nc'))[0]

        root_path, root_file = os.path.split(first_file)
        root_name, root_ext  = os.path.splitext(root_file)
        root_cell = re.findall(r'\d\d\d\d', root_file)[0]
        fn_format = root_name.replace(root_cell, '{:04d}')

        # version = os.path.basename(first_file).rsplit('_', 1)[0]
        # fn_format = '{:}_{{:04d}}'.format(version)

        grid_filename = os.path.join(grid_path, grid_filename)

        super(AscatDriverSsmCdr, self).__init__(cdr_path, fn_format,
                                                grid_filename,
                                                static_layer_path, **kwargs)

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to write data in a cell indexed file
class AscatDriverIndexed(GriddedNcTs):

    def __init__(self, *args, **kwargs):
        kwargs['ioclass'] = IndexedRaggedTs
        super(AscatDriverIndexed, self).__init__(*args, **kwargs)

    def write_cell(self, cell, gpi, data, datefield, filename_tmpl='%04d.nc'):
        """
        Write complete data set into cell file.

        Parameters
        ----------
        cell : int
            Cell number.
        gpi : numpy.ndarray
            Location ids.
        data : dict or numpy record array
            dictionary with variable names as keys and numpy.arrays as values
        datefield: string
            field in the data dict that contains dates in correct format
        """
        if isinstance(self.grid, CellGrid) is False:
            raise TypeError("Associated grid is not of type "
                            "pygeogrids.CellGrid.")

        if self.mode != 'w':
            raise ValueError("File not opened in write mode.")

        tmp_cell = np.unique(self.grid.arrcell[gpi])

        if tmp_cell.size > 1 or tmp_cell != cell:
            raise ValueError("GPIs do not correspond to given cell.")

        lons = self.grid.arrlon[gpi]
        lats = self.grid.arrlat[gpi]
        gpis = self.grid.gpis[gpi]

        gpis = gpis.data

        filename = os.path.join(self.path, filename_tmpl % cell)

        if os.path.isfile(filename):
            mode = 'a'
        else:
            mode = 'w'

        if self.previous_cell != cell:
            self.flush()
            self.close()
            self.previous_cell = cell
            if self.mode == 'w':
                if 'n_loc' not in self.ioclass_kws:
                    n_loc = self.grid.grid_points_for_cell(cell)[0].size
                    self.ioclass_kws['n_loc'] = n_loc
            self.fid = self.ioclass(filename, mode=mode,
                                    **self.ioclass_kws)
            self.ioclass_kws.pop('n_loc', None)

        if type(data) != dict:
            data = {key: data[key] for key in data.dtype.names}

        dates = data[datefield]
        del data[datefield]

        self.fid.write_ts(gpis, data, dates, lon=lons, lat=lats, dates_direct=True)

        self.flush()
        self.close()
# ----------------------------------------------------------------------------------------------------------------------
