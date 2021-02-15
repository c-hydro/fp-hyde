"""
Class Features

Name:          drv_data_ef_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201202'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import os
import json
import xarray as xr

from src.hyde.algorithm.analysis.expert_forecast.lib_ef_analysis import compute_slopes
from src.hyde.algorithm.geo.expert_forecast.lib_ef_geo import read_file_raster
from src.hyde.algorithm.io.expert_forecast.lib_ef_io_generic import write_obj, read_obj, read_file_mat
from src.hyde.algorithm.utils.expert_forecast.lib_ef_generic import make_folder

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Class to manage geographical datasets
class DriverGeo:

    def __init__(self, src_dict, ancillary_dict, dst_dict=None,
                 tag_folder_name='folder_name', tag_file_name='file_name',
                 tag_terrain_data='terrain',
                 tag_alert_area_data='alert_area', tag_slopes_data='slopes',
                 tag_ancillary_data_grid='grid_reference',
                 tag_ancillary_data_geo='geo_reference',
                 flag_updating_ancillary=True):

        self.src_dict = src_dict
        self.ancillary_dict = ancillary_dict
        self.dst_dict = dst_dict

        self.tag_folder_name = tag_folder_name
        self.tag_file_name = tag_file_name

        self.tag_terrain_data = tag_terrain_data
        self.tag_alert_area_data = tag_alert_area_data
        self.tag_slopes_data = tag_slopes_data
        self.tag_ancillary_data_grid = tag_ancillary_data_grid
        self.tag_ancillary_data_geo = tag_ancillary_data_geo

        self.flag_updating_ancillary = flag_updating_ancillary

        self.folder_name_terrain = src_dict[self.tag_terrain_data][self.tag_folder_name]
        self.file_name_terrain = src_dict[self.tag_terrain_data][self.tag_file_name]
        self.file_path_terrain = os.path.join(self.folder_name_terrain, self.file_name_terrain)

        self.folder_name_alert_area = src_dict[self.tag_alert_area_data][self.tag_folder_name]
        self.file_name_alert_area = src_dict[self.tag_alert_area_data][self.tag_file_name]
        self.file_path_alert_area = os.path.join(self.folder_name_alert_area, self.file_name_alert_area)

        self.folder_name_slopes = src_dict[self.tag_slopes_data][self.tag_folder_name]
        self.file_name_slopes = src_dict[self.tag_slopes_data][self.tag_file_name]
        self.file_path_slopes = os.path.join(self.folder_name_slopes, self.file_name_slopes)

        self.folder_name_ancillary_geo = ancillary_dict[self.tag_ancillary_data_geo][self.tag_folder_name]
        self.file_name_ancillary_geo = ancillary_dict[self.tag_ancillary_data_geo][self.tag_file_name]
        self.file_path_ancillary_geo = os.path.join(self.folder_name_ancillary_geo, self.file_name_ancillary_geo)

        self.folder_name_ancillary_grid = ancillary_dict[self.tag_ancillary_data_grid][self.tag_folder_name]
        self.file_name_ancillary_grid = ancillary_dict[self.tag_ancillary_data_grid][self.tag_file_name]
        self.file_path_ancillary_grid = os.path.join(self.folder_name_ancillary_grid, self.file_name_ancillary_grid)

        self.tag_dim_geo_x = 'longitude'
        self.tag_dim_geo_y = 'latitude'
        self.tag_coord_geo_x = 'west_east'
        self.tag_coord_geo_y = 'south_north'

        if self.flag_updating_ancillary:
            if os.path.exists(self.file_path_ancillary_geo):
                os.remove(self.file_path_ancillary_geo)
            if os.path.exists(self.file_path_ancillary_grid):
                os.remove(self.file_path_ancillary_grid)

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to write dataset in dictionary format
    @staticmethod
    def write_dset_obj(file_name, file_obj):
        if isinstance(file_obj, xr.Dataset):
            file_data = file_obj.to_dict()
        else:
            file_data = file_obj
        write_obj(file_name, file_data)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to load dataset saved in dictionary format
    @staticmethod
    def read_dset_obj(file_name, data_format='dictionary'):
        file_data = read_obj(file_name)
        if data_format == 'dataset':
            file_obj = xr.Dataset.from_dict(file_data)
        else:
            file_obj = file_data
        return file_obj
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get slopes data
    def get_slopes_data(self, file_path_statistics, var_name='slopes'):

        logging.info(' ----> Get ' + var_name + ' information ... ')

        if os.path.exists(file_path_statistics):

            var_vm = read_file_mat(file_path_statistics, var_name='vm')
            obj_vm = compute_slopes(var_vm)

            logging.info(' ----> Get ' + var_name + ' information ... DONE')
        else:
            logging.info(' ----> Get ' + var_name + ' information ... FAILED')
            logging.error(' ===> Error in finding ' + var_name + ' information')
            raise IOError('File not found')

        return obj_vm
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get geo data
    def get_geo_data(self, file_path_data, var_name='terrain'):

        logging.info(' ----> Get ' + var_name + ' information ... ')

        if os.path.exists(file_path_data):

            da_data, wide_data, high_data, proj_data, transform_data, bounding_box, no_data = read_file_raster(
                file_path_data,
                coord_name_x=self.tag_coord_geo_x, coord_name_y=self.tag_coord_geo_y,
                dim_name_x=self.tag_dim_geo_x, dim_name_y=self.tag_dim_geo_y, var_name=var_name)

            dset_data = da_data.to_dataset()

            attrs_data = {'wide': wide_data, 'high': high_data,
                          'proj': proj_data, 'transform': transform_data,
                          'bbox': bounding_box,
                          'no_data': no_data}

            dset_data.attrs = attrs_data

            logging.info(' ----> Get ' + var_name + ' information ... DONE')

        else:
            logging.info(' ----> Get ' + var_name + ' information ... FAILED')
            logging.error(' ===> Error in finding ' + var_name + ' information')
            raise IOError('File not found')

        return dset_data
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define geo attributes
    @staticmethod
    def define_geo_attributes(file_path_data, dset_data,
                              file_path_ancillary_grid, file_path_ancillary_geo):

        # Marche reference: iCols 643 iY jdim iRows 534 iX idim
        dset_attrs_raw = dset_data.attrs

        transform = dset_attrs_raw['transform']
        cellsize = transform[0]
        xllcorner = transform[2]
        yllcorner = transform[5]

        bbox = dset_attrs_raw['bbox']
        nrows = int(dset_attrs_raw['high'])  # high = dims[0] --> nrows
        ncols = int(dset_attrs_raw['wide'])  # wide = dims[1] --> cols
        nodata_value = dset_attrs_raw['no_data']
        proj = dset_attrs_raw['proj']

        dset_attrs_tmp = {
            'ncols': ncols, 'nrows': nrows,
            'xllcorner': xllcorner, 'yllcorner': yllcorner,
            'cellsize': cellsize, 'nodata_value': nodata_value, 'bounding_box': bbox,
            'proj': proj, 'transform': transform, 'file_path_data': file_path_data,
            'file_path_grid': file_path_ancillary_grid, 'file_path_geo': file_path_ancillary_geo}

        dset_attrs_valid = {}
        for dset_key, dset_value in dset_attrs_tmp.items():
            if isinstance(dset_value, list):
                dset_value_tmp = [str(value) for value in dset_value]
                dset_value = ','.join(dset_value_tmp)
            if isinstance(dset_value, dict):
                dset_value_tmp = json.dumps(dset_value)
                dset_value = dset_value_tmp
            dset_attrs_valid[dset_key] = dset_value
        return dset_attrs_valid
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compose geographical information
    def composer_geo(self):

        # Info start
        logging.info(' ---> Compose geographical information ... ')

        file_path_ancillary_geo = self.file_path_ancillary_geo

        geo_collections = {}
        if not os.path.exists(file_path_ancillary_geo):

            # Get geographical datasets
            dset_terrain = self.get_geo_data(self.file_path_terrain, var_name=self.tag_terrain_data)
            dset_alert_area = self.get_geo_data(self.file_path_alert_area, var_name=self.tag_alert_area_data)

            # Define attributes
            dset_terrain_attrs = self.define_geo_attributes(
                self.file_path_terrain, dset_terrain, self.file_path_ancillary_grid, self.file_name_ancillary_grid)
            dset_alert_area_attrs = self.define_geo_attributes(
                self.file_path_alert_area, dset_alert_area, self.file_path_ancillary_grid, self.file_name_ancillary_grid)

            # Add attributes to datasets
            dset_terrain.attrs = dset_terrain_attrs
            dset_alert_area.attrs = dset_alert_area_attrs

            # Get slopes datasets
            var_slopes = self.get_slopes_data(self.file_path_slopes, var_name=self.tag_slopes_data)

            # Compose geographical information
            geo_collections[self.tag_terrain_data] = dset_terrain
            geo_collections[self.tag_alert_area_data] = dset_alert_area
            geo_collections[self.tag_slopes_data] = var_slopes

            # Dump geographical collections
            self.write_dset_obj(file_path_ancillary_geo, geo_collections)

            logging.info(' ---> Compose geographical information ... DONE')

        else:
            geo_collections = self.read_dset_obj(file_path_ancillary_geo)
            logging.info(' ---> Compose geographical information ... DONE. Loaded using saved ancillary file')

        # info end
        logging.info(' ---> Compose geographical information ... DONE')

        return geo_collections

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
