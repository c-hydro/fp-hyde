"""
Class Features

Name:          drv_data_rs_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201210'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import os
import json
import numpy as np
import pandas as pd
import xarray as xr

from src.hyde.algorithm.geo.ground_network.lib_rs_geo import read_shapefile_points
from src.hyde.algorithm.io.ground_network.lib_rs_io_generic import write_obj, read_obj, convert_values2da
from src.hyde.algorithm.utils.ground_network.lib_rs_generic import make_folder

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Class to manage geographical datasets
class DriverGeo:

    def __init__(self, src_dict, ancillary_dict, dst_dict=None,
                 tag_folder_name='folder_name', tag_file_name='file_name',
                 tag_file_fields_columns='file_fields_columns', tag_file_fields_types='file_fields_types',
                 tag_file_fields_tags='file_fields_tags',
                 tag_src_data='sections',
                 tag_ancillary_data='points',
                 flag_updating_ancillary=True):

        self.src_dict = src_dict
        self.ancillary_dict = ancillary_dict
        self.dst_dict = dst_dict

        self.tag_folder_name = tag_folder_name
        self.tag_file_name = tag_file_name
        self.tag_file_fields_columns = tag_file_fields_columns
        self.tag_file_fields_types = tag_file_fields_types
        self.tag_file_fields_tags = tag_file_fields_tags

        self.tag_src_data = tag_src_data
        self.tag_ancillary_data = tag_ancillary_data

        self.flag_updating_ancillary = flag_updating_ancillary

        self.folder_name_data = src_dict[self.tag_src_data][self.tag_folder_name]
        self.file_name_data = src_dict[self.tag_src_data][self.tag_file_name]
        self.file_path_data = os.path.join(self.folder_name_data, self.file_name_data)

        self.folder_name_ancillary = ancillary_dict[self.tag_ancillary_data][self.tag_folder_name]
        self.file_name_ancillary = ancillary_dict[self.tag_ancillary_data][self.tag_file_name]
        self.file_path_ancillary = os.path.join(self.folder_name_ancillary, self.file_name_ancillary)

        self.tag_dim_geo_x = 'longitude'
        self.tag_dim_geo_y = 'latitude'

        if self.tag_file_fields_columns in list(src_dict[self.tag_src_data].keys()):
            self.columns_name_expected = src_dict[self.tag_src_data][self.tag_file_fields_columns]
        else:
            self.columns_name_expected = [
                'ID', 'HMC_X', 'HMC_Y', 'LON', 'LAT',
                'BASIN', 'SEC_NAME', 'SEC_RS', 'SEC_TAG', 'TYPE', 'AREA', 'Q_THR1', 'Q_THR2',
                'ADMIN_B_L1', 'ADMIN_B_L2', 'ADMIN_B_L3']

        if self.tag_file_fields_types in list(src_dict[self.tag_src_data].keys()):
            columns_name_tmp = src_dict[self.tag_src_data][self.tag_file_fields_types]
            self.columns_name_type = self.convert_name2type(columns_name_tmp)
        else:
            self.columns_name_type = [
                np.int, np.int, np.int, np.float, np.float,
                str, str, np.int, str, str, np.float, np.float, np.float,
                str, str, str]

        if self.tag_file_fields_tags in list(src_dict[self.tag_src_data].keys()):
            self.columns_name_tag = src_dict[self.tag_src_data][self.tag_file_fields_tags]
        else:
            self.columns_name_tag = [
                'id', 'hmc_id_x', 'hmc_id_y', 'longitude', 'latitude',
                'catchment', 'name', 'code', 'tag', 'type', 'area', 'discharge_thr1', 'discharge_thr2',
                'boundary_limit_01', 'boundary_limit_02', 'boundary_limit_03']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to convert name in type format
    @staticmethod
    def convert_name2type(columns_list_name):
        columns_list_type = []
        for field_name in columns_list_name:
            if field_name == 'int':
                columns_list_type.append(np.int)
            elif field_name == 'float':
                columns_list_type.append(np.float)
            elif field_name == 'str':
                columns_list_type.append(str)
            else:
                logging.error(' ===> Name "' + field_name + '" is not supported by known type')
                raise NotImplementedError('Case not implemented yet')
        return columns_list_type
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to write dataset in dictionary format
    @staticmethod
    def write_dset_obj(file_name, file_df):
        file_dict = file_df.to_dict()
        write_obj(file_name, file_dict)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to load dataset saved in dictionary format
    @staticmethod
    def read_dset_obj(file_name):
        file_dict = read_obj(file_name)
        file_df = pd.DataFrame.from_dict(file_dict)
        return file_df
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define geo reference
    def define_geo_ref(self, var_name='sections'):

        logging.info(' ----> Get sections information ... ')

        file_path_data = self.file_path_data
        file_path_ancillary = self.file_path_ancillary

        if self.flag_updating_ancillary:
            if os.path.exists(file_path_ancillary):
                os.remove(file_path_ancillary)

        if os.path.exists(file_path_data):
            if not os.path.exists(file_path_ancillary):

                df_points = read_shapefile_points(file_path_data,
                                                  columns_name_expected=self.columns_name_expected,
                                                  columns_name_type=self.columns_name_type,
                                                  columns_name_tag=self.columns_name_tag)

                self.write_dset_obj(file_path_ancillary, df_points)

                logging.info(' ----> Get sections information ... DONE')

            else:
                df_points = self.read_dset_obj(file_path_ancillary)
                logging.info(' ----> Get sections information ... DONE. Loaded using saved ancillary file')
        else:
            logging.info(' ----> Get sections information ... FAILED')
            logging.error(' ===> Error in finding sections information')
            raise IOError('File not found')

        return df_points
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define geo attributes
    @staticmethod
    def define_geo_attributes(dset_sections):

        dset_attrs_tmp = dset_sections.attrs

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

        # Define land datasets
        df_collections = self.define_geo_ref()

        # Define attributes
        df_attrs = self.define_geo_attributes(df_collections)

        # Merge land and predictors datasets
        df_collections.attrs = df_attrs

        # info end
        logging.info(' ---> Compose geographical information ... DONE')

        return df_collections

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
