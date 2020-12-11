"""
Class Features

Name:          drv_data_mcm_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201206'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import os
import json
import xarray as xr

from src.hyde.algorithm.geo.radar.lib_mcm_geo import read_file_raster
from src.hyde.algorithm.io.radar.lib_mcm_io_generic import write_obj, read_obj, convert_values2da
from src.hyde.algorithm.utils.radar.lib_mcm_generic import make_folder

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Class to manage geographical datasets
class DriverGeo:

    def __init__(self, src_dict, ancillary_dict, dst_dict=None,
                 tag_folder_name='folder_name', tag_file_name='file_name',
                 tag_src_data='terrain',
                 tag_ancillary_data_grid='grid_reference',
                 tag_ancillary_data_geo='geo_reference',
                 flag_updating_ancillary=True):

        self.src_dict = src_dict
        self.ancillary_dict = ancillary_dict
        self.dst_dict = dst_dict

        self.tag_folder_name = tag_folder_name
        self.tag_file_name = tag_file_name

        self.tag_src_data = tag_src_data
        self.tag_ancillary_data_grid = tag_ancillary_data_grid
        self.tag_ancillary_data_geo = tag_ancillary_data_geo

        self.flag_updating_ancillary = flag_updating_ancillary

        self.folder_name_land = src_dict[self.tag_src_data][self.tag_folder_name]
        self.file_name_land = src_dict[self.tag_src_data][self.tag_file_name]
        self.file_path_land = os.path.join(self.folder_name_land, self.file_name_land)

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
    def write_dset_obj(file_name, file_dset):
        file_dict = file_dset.to_dict()
        write_obj(file_name, file_dict)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to load dataset saved in dictionary format
    @staticmethod
    def read_dset_obj(file_name):
        file_dict = read_obj(file_name)
        file_dset = xr.Dataset.from_dict(file_dict)
        return file_dset
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define geo reference
    def define_geo_ref(self, var_name='terrain'):

        logging.info(' ----> Get land information ... ')

        file_path_land = self.file_path_land
        file_path_ancillary_geo = self.file_path_ancillary_geo

        if os.path.exists(file_path_land):
            if not os.path.exists(file_path_ancillary_geo):

                da_land, wide_land, high_land, proj_land, transform_land, bounding_box, no_data_land = read_file_raster(
                    file_path_land,
                    coord_name_x=self.tag_coord_geo_x, coord_name_y=self.tag_coord_geo_y,
                    dim_name_x=self.tag_dim_geo_x, dim_name_y=self.tag_dim_geo_y, var_name=var_name)

                dset_land = da_land.to_dataset()

                attrs_land = {'wide': wide_land, 'high': high_land,
                              'proj': proj_land, 'transform': transform_land,
                              'bbox': bounding_box,
                              'no_data': no_data_land}

                dset_land.attrs = attrs_land
                self.write_dset_obj(file_path_ancillary_geo, dset_land)

                logging.info(' ----> Get land information ... DONE')

            else:
                dset_land = self.read_dset_obj(file_path_ancillary_geo)
                logging.info(' ----> Get land information ... DONE. Loaded using saved ancillary file')
        else:
            logging.info(' ----> Get land information ... FAILED')
            logging.error(' ===> Error in findind land information')
            raise IOError('File not found')

        return dset_land
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define geo attributes
    def define_geo_attributes(self, dset_land):

        # Marche reference: iCols 643 iY jdim iRows 534 iX idim
        dset_attrs_raw = dset_land.attrs

        transform = dset_attrs_raw['transform']
        cellsize = transform[0]
        xllcorner = transform[2]
        yllcorner = transform[5]

        bbox = dset_attrs_raw['bbox']
        nrows = int(dset_attrs_raw['high'])  # high = dims[0] --> nrows
        ncols = int(dset_attrs_raw['wide'])  # wide = dims[1] --> cols
        nodata_value = dset_attrs_raw['no_data']
        proj = dset_attrs_raw['proj']

        file_path_land = self.file_path_land
        file_path_ancillary_grid = self.file_path_ancillary_grid
        file_path_ancillary_geo = self.file_path_ancillary_geo

        dset_attrs_tmp = {
            'ncols': ncols, 'nrows': nrows,
            'xllcorner': xllcorner, 'yllcorner': yllcorner,
            'cellsize': cellsize, 'nodata_value': nodata_value, 'bounding_box': bbox,
            'proj': proj, 'transform': transform, 'file_path_ref': file_path_land,
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

        # Define datasets
        dset_collections = self.define_geo_ref()

        # Define attributes
        dset_attrs = self.define_geo_attributes(dset_collections)

        # Add attributes to geographical datasets collection
        dset_collections.attrs = dset_attrs

        # info end
        logging.info(' ---> Compose geographical information ... DONE')

        return dset_collections

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
