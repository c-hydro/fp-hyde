# -------------------------------------------------------------------------------------
# Library
import os
import numpy as np

from numpy.lib.recfunctions import append_fields, rename_fields, drop_fields

from pygeogrids.netcdf import load_grid

from src.hyde.algorithm.utils.satellite.hsaf.lib_ascat_generic import fill_tags2string, delete_file_cell

from src.hyde.dataset.satellite.ascat.lib_ascat_resempler_apps import OrbitResampler
from src.hyde.dataset.satellite.ascat.lib_ascat_driver_interface_obs import AscatDriverH16, AscatDriverH101, \
    AscatDriverIndexed
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to set ascat swath data (h16, h101, h102, h103)
class AscatResamplerConfigure:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, time_run,
                 ascat_product,
                 ascat_path_swath,
                 ascat_path_ts,
                 ascat_filename_ts='{cell}.nc',
                 grid_path='/',
                 grid_filename='TUW_WARP5_grid_info_2_3.nc',
                 ascat_month_path_str='%Y/%m/%d/%H/',
                 writing_mode='w',
                 mask=True,
                 tmpl_tags=None,
                 tmpl_values=None,
                 time_start=None, time_end=None,
                 ascat_updating_ts=False):

        # Set time information
        self.time_run = time_run

        if time_start is None:
            time_start = self.time_run
        if time_end is None:
            time_end = self.time_run

        self.time_start = time_start
        self.time_end = time_end

        # Set tag(s) and value(s) template
        if tmpl_tags is None:
            tmpl_tags = {'datetime': '%Y%m%d%H%M', 'sub_path_time': '%Y/%m/%d', 'cell': '%04d',
                         'time_start': 'from_%Y%m%d%H%M', 'time_end': 'to_%Y%m%d%H%M'}
        self.tmpl_tags = tmpl_tags
        if tmpl_values is None:
            tmpl_values = {'datetime':  None, 'sub_path_time': None, 'cell': None,
                           'time_start': self.time_start, 'time_end': self.time_end}
        self.tmpl_values = tmpl_values

        # Select product driver(s)
        ascat_io_lut = {
            'h16': AscatDriverH16,
            'h101': AscatDriverH101,
            'h102': None,
            'h103': None}

        # Compute target grid
        self.target_grid = load_grid(os.path.join(grid_path, grid_filename))
        self.target_cells = np.unique(self.target_grid.activearrcell)

        # Initialize product swath class
        ascat_io_class = ascat_io_lut[ascat_product]
        self.ascat_io_swath = ascat_io_class(
            ascat_path_swath,
            month_path_str=ascat_month_path_str,
            chunk_minutes=50)

        # Define ts path and filename
        tmpl_values['sub_path_time'] = self.time_run
        tmpl_values['datetime'] = self.time_run
        ascat_path_ts = fill_tags2string(ascat_path_ts, self.tmpl_tags, tmpl_values)

        ascat_filename_ts = fill_tags2string(ascat_filename_ts, self.tmpl_tags, tmpl_values)
        if not os.path.exists(ascat_path_ts):
            os.makedirs(ascat_path_ts)
        self.ascat_path_ts = ascat_path_ts
        self.ascat_filename_ts = ascat_filename_ts

        # Initialize product indexed class
        self.ascat_io_ts = AscatDriverIndexed(
            ascat_path_ts,
            grid=self.target_grid,
            mode=writing_mode,
            ioclass_kws={'time_units': "days since 1858-11-17 00:00:00"})

        # Define time stamps
        self.time_stamps = np.array(self.ascat_io_swath.tstamps_for_daterange(time_start, time_end))
        # Set mask flag
        self.mask = mask
        # Set updating flag
        self.ascat_updating_ts = ascat_updating_ts

        if self.ascat_updating_ts:
            delete_file_cell(self.ascat_path_ts, filename_ts=self.ascat_filename_ts,
                             cells=self.target_cells)

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to resample data from swath to ts format
    def resampler(self, write_n_resampled=2000, write_orbit_buffer=True):

        resampler = AscatResamplerInterface(
            self.ascat_io_swath, self.ascat_io_ts,
            spatial_res=25000,
            dt=15,
            wfunc='hamming',
            write_orbit_buffer=write_orbit_buffer,
            mask=self.mask,
            filename_tmpl=self.ascat_filename_ts)

        resampler.resample(self.time_stamps, write_n_resampled=write_n_resampled)

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to resample ascat swath data (h16, h101, h102, h103)
class AscatResamplerInterface(OrbitResampler):
    """
    Resample ASCAT Orbits to time series while also performing SSF
    retrieval.

    Parameters
    ----------
    orbit_io : Subclass of MultiTemporalImageBase
        Orbit file reader.
    resam_usort_io : Subclass of GriddedTsBase
        Re-sampled data writer, has to support the write_cell method.
    spatial_res: int, optional
        spatial resolution in meters
    wfunc: string, optional
        one of 'hamming', 'boxcar'
    min_num_nn: int, optional
        Minimum number of nearest neighbors to be found to use the data
        from the swath/orbit
    dt: int, optional
        Temporal distance in minutes between two files so that they
        should be considered temporal neighbors
    """

    def __init__(self, orbit_io, resam_io, spatial_res=25000.,
                 wfunc='hamming', min_num_nn=3, dt=15,
                 write_orbit_buffer=False, mask=False, filename_tmpl='{:}.nc'):

        super(AscatResamplerInterface, self).__init__(
            orbit_io, resam_io,
            spatial_res=spatial_res,
            wfunc=wfunc,
            min_num_nn=min_num_nn,
            dt=dt,
            write_orbit_buffer=write_orbit_buffer,
            mask=mask,
            filename_tmpl=filename_tmpl)

    def resample(self, time_stamps, write_n_resampled=14 * 2 * 365):
        """
        Run re-sampling for given time_stamps.
        Data is written if available memory becomes low
        or if write_n_resampled files have been resampled.

        Parameters
        ----------
        time_stamps : numpy.ndarray
            Orbit time stamp information.
        write_n_resampled: int, optional
            Write data if more than n timestamps have been resampled.
            The default is one year of ASCAT data at the moment.
        proc_param : dict
            Processing parameters.

        Returns
        -------
        resampled_timestamps: list
            list of resampled timestamps that actually contained
            data on the target grid
        """
        super(AscatResamplerInterface, self).resample(
            time_stamps,
            write_n_resampled=write_n_resampled)

    def resample_orbit(self, timestamp):
        """
        Resample orbit.
        """

        gpis, orbit = super(AscatResamplerInterface,
                            self).resample_orbit(timestamp)

        return gpis, orbit

    def write_resampled_data(self, gpi_data, orbit_data):
        """
        write the data after name conversion.

        Parameters
        ----------
        gpi_data : numpy.recarray
            Grid point information. A grid point indices
            for each element in the orbit data array.
        orbit_data : numpy.recarray
            record array containing the resampled data at the grid point
            indices of gpi_data
        """
        orbit_data['Soil Moisture Processing Flag'] = (
            translate_processing_flag(
                orbit_data['Soil Moisture Processing Flag']))

        fields_to_rename = {
            'Surface Soil Moisture (Ms)': 'sm',
            'Estimated Error In Surface Soil Moisture': 'sm_noise',
            'Soil Moisture Correction Flag': 'corr_flag',
            'Soil Moisture Processing Flag': 'proc_flag',
            'Direction Of Motion Of Moving Observing Platform': 'dir'}
        orbit_data = rename_fields(orbit_data, fields_to_rename)

        fields_to_keep = ['sm', 'sm_noise', 'dir',
                          'corr_flag', 'proc_flag', 'jd']
        fields_to_drop = set(orbit_data.dtype.names).difference(fields_to_keep)
        orbit_data = drop_fields(orbit_data, fields_to_drop)

        # convert to modified julian date
        orbit_data['jd'] = orbit_data['jd'] - 2400000.5
        # convert direction to ascending/descending flag
        orbit_data['dir'] = orbit_data['dir'] < 270
        super(AscatResamplerInterface, self).write_resampled_data(
            gpi_data, orbit_data)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to shift bits
def translate_processing_flag(proc_flag_orbit):
    """
    Shift bits by one position since orbit processing
    flag contain a flag at bit 0 that does not exist
    in the time series format.
    """
    proc_flag_ts = np.right_shift(proc_flag_orbit.astype(np.uint8), 1)
    return proc_flag_ts
# -------------------------------------------------------------------------------------
