# -------------------------------------------------------------------------------------
# Libraries
import logging
import os
import numpy as np

from bin.downloader.ground_network.mysql.lib_utils_geo import read_data_shapefile_dam
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class driver geographical data
class DriverGeo:

    def __init__(self, src_dict, dst_dict=None, tag_geo_sections='sections'):

        self.src_dict = src_dict
        self.dst_dict = dst_dict

        self.tag_geo_sections = tag_geo_sections
        self.tag_folder_name = 'folder_name'
        self.tag_file_name = 'file_name'

        self.folder_name = self.src_dict[self.tag_geo_sections][self.tag_folder_name]
        self.file_name = self.src_dict[self.tag_geo_sections][self.tag_file_name]

        self.file_path = os.path.join(self.folder_name, self.file_name)

        self.columns_name_expected = ['HMC_X', 'HMC_Y', 'LON', 'LAT', 'BASIN', 'NAME', 'CODE', 'TAG', 'TYPE', 'AREA']
        self.columns_name_type = [np.int, np.int, np.float, np.float, str, str, np.int, str, str, np.float]

        self.columns_name_tag = ['hmc_id_x', 'hmc_id_y', 'longitude', 'latitude',
                                 'catchment', 'name', 'code', 'tag', 'type', 'area']

    # Method to read sections datasets
    def read_data(self):

        logging.info(' ----> Read dams file ' + self.file_name + ' ... ')
        if os.path.exists(self.file_path):
            dams_obj = read_data_shapefile_dam(
                self.file_path,
                columns_name_expected=self.columns_name_expected,
                columns_name_type=self.columns_name_type,
                columns_name_tag=self.columns_name_tag)
            logging.info(' ----> Read dams file ' + self.file_name + ' ... DONE')
        else:
            logging.error(' ==> Read dams file ' + self.file_name + ' ... FAILED')
            raise IOError('File does not exist')
        return dams_obj
# -------------------------------------------------------------------------------------
