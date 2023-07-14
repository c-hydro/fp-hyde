"""
Library Features:

Name:          cpl_data_variables_ws
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180918'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import inspect

import numpy as np
import pandas as pd

from copy import deepcopy

import src.hyde.dataset.ground_network.ws.lib_ws_variables as fx_collections

# Debug
# import matplotlib.pylab as plt
#################################################################################


# -------------------------------------------------------------------------------------
# Class to drive variable
class DriverVariable:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, var_obj, ref_obj, var_attributes=None,
                 fx_name=None, fx_parameters=None, fx_outcome=None,
                 tag_var_geo_x='longitude', tag_var_geo_y='latitude', tag_var_geo_z='altitude',
                 tag_ref_geo_x='west_east', tag_ref_geo_y='south_north',
                 tag_var_ws_data='data',
                 tag_ref_land_data='land_data', tag_ref_aspect_data='aspect_data',
                 tag_ref_slope_data='slope_data', tag_ref_hillshade_data='hillshade_data',
                 ):

        self.var_obj = var_obj
        self.ref_obj = ref_obj

        self.var_attributes = var_attributes
        self.fx_name = fx_name
        self.fx_parameters = fx_parameters
        self.fx_outcome = fx_outcome

        self.tag_var_geo_x = tag_var_geo_x
        self.tag_var_geo_y = tag_var_geo_y
        self.tag_var_geo_z = tag_var_geo_z

        self.tag_var_ws_data = tag_var_ws_data

        self.tag_ref_geo_x = tag_ref_geo_x
        self.tag_ref_geo_y = tag_ref_geo_y

        self.tag_ref_land_data = tag_ref_land_data
        self.tag_ref_aspect_data = tag_ref_aspect_data
        self.tag_ref_slope_data = tag_ref_slope_data
        self.tag_ref_hillshade_data = tag_ref_hillshade_data

        self.var_valid_range, self.var_missing_value, \
            self.var_fill_value, self.var_units = self.get_var_attributes()

        self.ref_proj, self.ref_transform, \
            self.ref_cellsize_x, self.ref_cellsize_y, self.ref_nodata = self.get_ref_attributes()

        self.fx_nodata, self.fx_interp_name, self.fx_interp_radius_x, self.fx_interp_radius_y, \
            self.fx_regression_radius_influence, self.fx_cpu, self.fx_idw_coeff = self.get_fx_attributes()
        self.fx_obj = self.get_fx_method()

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get ref attributes
    def get_ref_attributes(self):

        ref_proj = self.ref_obj.attrs['proj']
        ref_transform = self.ref_obj.attrs['transform']
        ref_nodata = self.ref_obj.attrs['nodata_value']

        ref_cellsize_x = ref_transform[0]
        ref_cellsize_y = -ref_transform[4]

        if ref_cellsize_x != ref_cellsize_y:
            logging.warning(' ===> X cell-size and Y cell-size are different; compute mean(X,Y) cell-size')
            ref_cellsize_mean = np.mean([ref_cellsize_x, ref_cellsize_y])
            ref_cellsize_x = ref_cellsize_mean
            ref_cellsize_y = ref_cellsize_mean

        return ref_proj, ref_transform, ref_cellsize_x, ref_cellsize_y, ref_nodata

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to filter variable
    def filter_var_valid_range(self, var_dframe):

        if self.var_valid_range is not None:
            if self.var_valid_range[0] is not None:
                try:
                    var_dframe = var_dframe[var_dframe[self.tag_var_ws_data] >= self.var_valid_range[0]]
                except KeyError:
                    if var_dframe[self.tag_var_ws_data] >= self.var_valid_range[0]:
                        pass
                    else:
                        var_dframe = []
            if self.var_valid_range[1] is not None:
                try:
                    var_dframe = var_dframe[var_dframe[self.tag_var_ws_data] <= self.var_valid_range[1]]
                except KeyError:
                    if var_dframe[self.tag_var_ws_data] >= self.var_valid_range[0]:
                        pass
                    else:
                        var_dframe = []
        else:
            logging.warning(' ===> Skipping data filtering due to an undefined valid range attribute')
        if isinstance(var_dframe, pd.Series):
            var_dframe = var_dframe.to_frame().T
        var_dframe = var_dframe.dropna()
        return var_dframe

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get var attributes
    def get_var_attributes(self):

        # Parser method argument(s)
        var_valid_range = None
        if 'valid_range' in list(self.var_attributes.keys()):
            var_valid_range = self.var_attributes['valid_range']
        else:
            logging.warning(' ===> Variable valid range is not defined')
        var_missing_value = -9999.0
        if 'missing_value' in list(self.var_attributes.keys()):
            var_missing_value = self.var_attributes['missing_value']
        else:
            logging.warning(' ===> Variable missing value is not defined')
        var_fill_value = -9999.0
        if 'fill_value' in list(self.var_attributes.keys()):
            var_fill_value = self.var_attributes['fill_value']
        else:
            logging.warning(' ===> Variable fill value is not defined')
        var_units = None
        if 'units' in list(self.var_attributes.keys()):
            var_units = self.var_attributes['units']
        else:
            logging.warning(' ===> Variable units are not defined')

        return var_valid_range, var_missing_value, var_fill_value, var_units

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get fx object
    def organize_fx_result(self, fx_result):

        fx_outcome = self.fx_outcome

        fx_result_obj = {}
        if isinstance(fx_result, np.ndarray):
            if isinstance(fx_outcome, str):
                fx_result_obj[fx_outcome] = fx_result
            else:
                logging.error(' ===> Fx outcome is not correctly defined. Expected string variable.')
                raise NotImplementedError('Definition case not supported yet')
        elif isinstance(fx_result, tuple):
            if isinstance(fx_outcome, list):
                for var_id, var_name in enumerate(fx_outcome):
                    var_data = fx_result[var_id]
                    fx_result_obj[var_name] = var_data
            else:
                logging.error(' ===> Fx outcome is not correctly defined. Expected list variable.')
                raise NotImplementedError('Definition case not supported yet')
        else:
            logging.error(' ===> Fx results are in wrong format.')
            raise NotImplementedError('Datasets case not supported yet')

        return fx_result_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get fx object
    def get_fx_method(self):

        if hasattr(fx_collections, self.fx_name):
            fx_obj = getattr(fx_collections, self.fx_name)
        else:
            logging.warning(' ===> Fx method is not available in the fx collections')
            fx_obj = None
        return fx_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get fx attributes
    def get_fx_attributes(self):

        fx_nodata = -9999.0
        if 'interp_nodata' in list(self.fx_parameters.keys()):
            fx_nodata = self.fx_parameters['interp_nodata']
        fx_interp_name = None
        if 'interp_method' in list(self.fx_parameters.keys()):
            fx_interp_name = self.fx_parameters['interp_method']
        fx_interp_radius_x = 0.0
        if 'interp_radius_x' in list(self.fx_parameters.keys()):
            fx_interp_radius_x = self.fx_parameters['interp_radius_x']
        fx_interp_radius_y = 0.0
        if 'interp_radius_y' in list(self.fx_parameters.keys()):
            fx_interp_radius_y = self.fx_parameters['interp_radius_y']
        fx_regression_radius_influence = 0.0
        if 'regression_radius_influence' in list(self.fx_parameters.keys()):
            fx_regression_radius_influence = self.fx_parameters['regression_radius_influence']
        fx_cpu = 1
        if 'cpu' in list(self.fx_parameters.keys()):
            fx_cpu = self.fx_parameters['cpu']
        fx_idw_coeff = None
        if 'idw_coeff' in list(self.fx_parameters.keys()):
            fx_idw_coeff = self.fx_parameters['idw_coeff']

        return fx_nodata, fx_interp_name, fx_interp_radius_x, fx_interp_radius_y, fx_regression_radius_influence, fx_cpu, fx_idw_coeff

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to fill fx args included in fx signature
    @staticmethod
    def fill_fx_args(fx_signature, fx_data):

        for fx_parameter in fx_signature.parameters.values():
            fx_parameter_name = fx_parameter.name
            fx_parameter_default = fx_parameter.default

            if fx_parameter_name not in list(fx_data.keys()):
                if fx_parameter_default is not inspect._empty:
                    fx_data[fx_parameter_name] = fx_parameter_default
                    logging.warning(' ===> Fx parameter not defined; fx will use a default value')
                else:
                    fx_data[fx_parameter_name] = None
                    logging.warning(' ===> Fx parameter not defined and default value is empty; fx will use null value')

        return fx_data

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to remove fx args not included in fx signature
    @staticmethod
    def pop_fx_args(fx_signature, fx_data):

        fx_data_tmp = deepcopy(fx_data)
        for fx_key_tmp in fx_data_tmp.keys():
            if fx_key_tmp not in list(fx_signature.parameters.keys()):
                fx_data.pop(fx_key_tmp, None)

        return fx_data
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable data
    def compute_data(self):

        # Get geographical data
        ref_obj = self.ref_obj

        # Get data filtered obj
        var_obj = deepcopy(self.filter_var_valid_range(self.var_obj))

        if self.fx_obj:

            # Get fx signature
            fx_signature = inspect.signature(self.fx_obj)
            # Create fx data
            fx_data = {'var_data': var_obj[self.tag_var_ws_data].values,
                       'var_geo_x': var_obj[self.tag_var_geo_x].values,
                       'var_geo_y': var_obj[self.tag_var_geo_y].values,
                       'var_geo_z': var_obj[self.tag_var_geo_z].values,
                       'var_units': self.var_units,
                       'var_missing_value': self.var_missing_value, 'var_fill_value': self.var_fill_value,
                       'fx_nodata': self.fx_nodata, 'fx_interp_name': self.fx_interp_name,
                       'fx_interp_radius_x': self.fx_interp_radius_x, 'fx_interp_radius_y': self.fx_interp_radius_y,
                       'fx_idw_coeff': self.fx_idw_coeff,
                       'fx_regression_radius_influence': self.fx_regression_radius_influence,
                       'ref_geo_x': ref_obj[self.tag_ref_geo_x].values,
                       'ref_geo_y': ref_obj[self.tag_ref_geo_y].values,
                       'ref_geo_z': ref_obj[self.tag_ref_land_data].values,
                       'ref_geo_aspect': ref_obj[self.tag_ref_aspect_data].values,
                       'ref_geo_slope': ref_obj[self.tag_ref_slope_data].values,
                       'ref_geo_hillshade': ref_obj[self.tag_ref_hillshade_data].values,
                       'ref_cell_size': np.mean([self.ref_cellsize_x, self.ref_cellsize_y]),
                       'ref_no_data': self.ref_nodata, 'ref_epsg': '4326',
                       'fx_cpu': self.fx_cpu
                       }

            # Fill and pop fx data
            fx_data = self.fill_fx_args(fx_signature, fx_data)
            fx_data = self.pop_fx_args(fx_signature, fx_data)
            # Execute fx method
            fx_results_data = self.fx_obj(**fx_data)

            # Organize fx result
            fx_results_collections = self.organize_fx_result(fx_results_data)

        else:
            logging.warning(' ===> Fx method is not defined. Fx results will be null')
            fx_results_collections = None

        return fx_results_collections
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
