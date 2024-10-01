# ----------------------------------------------------------------------------------------------------------------------
# Library
import warnings
import numpy as np
import os

try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")

from pygeobase.io_base import ImageBase, MultiTemporalImageBase
from pygeobase.object_base import Image
import pygeogrids
from pynetcf.time_series import GriddedNcOrthoMultiTs

from datetime import timedelta

from src.hyde.algorithm.geo.satellite.hsaf.lib_ascat_geo import load_grid_rzsm
from netCDF4 import Dataset
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to read a image
class AscatImg(ImageBase):

    def __init__(self, filename, mode='r', parameter='var_0_7', array_1D=False,
                 path_grid=None, filename_grid=None):

        super(AscatImg, self).__init__(filename, mode=mode)

        if type(parameter) != list:
            parameter = [parameter]
        self.path_grid = path_grid
        self.filename_grid = filename_grid
        self.parameters = parameter
        self.fill_values = np.repeat(9999., 0)
        self.grid = load_grid_rzsm(self.path_grid, self.filename_grid)
        self.array_1D = array_1D

    def read(self, timestamp=None):

        # print 'read file: %s' %self.filename
        # Returns the selected parameters for a gldas image and according metadata
        return_img = {}
        return_metadata = {}

        try:
            dataset = Dataset(self.filename)
        except IOError as e:
            print(e)
            print(" ".join([self.filename, "can not be opened"]))
            raise e

        param_names = []
        for parameter in self.parameters:
            param_names.append(parameter)

        for parameter, variable in dataset.variables.items():
            if parameter in param_names:
                param_metadata = {}
                param_data = {}
                for attrname in variable.ncattrs():
                    if attrname in ['long_name', 'units']:
                        param_metadata.update({str(attrname): getattr(variable, attrname)})

                param_data = dataset.variables[parameter][:]
                param_data = param_data[0, :, :]
                np.ma.set_fill_value(param_data, 9999)

                param_data = np.concatenate((self.fill_values,
                                             param_data.flatten()))

                return_img.update({str(parameter): param_data[self.grid.activegpis]})
                return_metadata.update({str(parameter): param_metadata})

                # Check for corrupt files
                try:
                    return_img[parameter]
                except KeyError:
                    path, thefile = os.path.split(self.filename)
                    print('%s in %s is corrupt - filling image with NaN values' % (parameter, thefile))
                    return_img[parameter] = np.empty(self.grid.n_gpi).fill(np.nan)
                    return_metadata['corrupt_parameters'].append()

        dataset.close()
        if self.array_1D:

            img = Image(self.grid.activearrlon, self.grid.activearrlat,
                        return_img, return_metadata, timestamp)
            return img
        else:
            for key in return_img:
                return_img[key] = np.flipud(return_img[key].reshape((720, 1440)))

            return Image(np.flipud(self.grid.activearrlon.reshape((720, 1440))),
                         np.flipud(self.grid.activearrlat.reshape((720, 1440))),
                         return_img,
                         return_metadata,
                         timestamp)

    def write(self, data):
        raise NotImplementedError()

    def flush(self):
        pass

    def close(self):
        pass

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to read multitemporal image(s)
class AscatDs(MultiTemporalImageBase):

    def __init__(self, data_path, data_filename_tmpl='rzsm_{datetime}.nc',
                 parameter='var_0_7', array_1D=False,
                 path_grid=None, filename_grid=None,
                 data_subpath_tmpl=['%Y/%m/%d'], datetime_format="%Y%m%d%H%M"):

        ioclass_kws = {'parameter': parameter,
                       'array_1D': array_1D,
                       'path_grid': path_grid,
                       'filename_grid': filename_grid,
                       }

        if not isinstance(data_subpath_tmpl, list):
            data_subpath_tmpl = [data_subpath_tmpl]

        super(AscatDs, self).__init__(data_path, AscatImg,
                                      fname_templ=data_filename_tmpl,
                                      datetime_format=datetime_format,
                                      subpath_templ=data_subpath_tmpl,
                                      exact_templ=False,
                                      ioclass_kws=ioclass_kws)

    def tstamps_for_daterange(self, start_date, end_date):

        img_offsets = np.array([timedelta(hours=0)])

        timestamps = []
        diff = end_date - start_date
        for i in range(diff.days + 1):
            daily_dates = start_date + timedelta(days=i) + img_offsets
            timestamps.extend(daily_dates.tolist())

        return timestamps

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to read a time-series
class AscatTs(GriddedNcOrthoMultiTs):

    def __init__(self, ts_path, grid_path=None, ts_name='%04d', grid_name='grid.nc'):

        fn_tmpl_format = '{:04d}'

        if grid_path is None:
            grid_path = os.path.join(ts_path, grid_name)
        else:
            grid_path = os.path.join(grid_path, grid_name)

        if '%04d' in ts_name:
            fn_format = ts_name.replace('%04d', fn_tmpl_format)
        else:
            fn_format = fn_tmpl_format

        grid = pygeogrids.netcdf.load_grid(grid_path)
        super(AscatTs, self).__init__(ts_path, grid, fn_format=fn_format)
# ----------------------------------------------------------------------------------------------------------------------
