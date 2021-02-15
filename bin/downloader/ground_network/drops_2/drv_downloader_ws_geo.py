# -------------------------------------------------------------------------------------
# Libraries
import logging
import os

from bin.downloader.ground_network.drops_2.lib_utils_geo import get_file_raster
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class driver geographical data
class DriverGeo:

    def __init__(self, src_dict, dst_dict=None, tag_geo_land='land'):

        self.src_dict = src_dict
        self.dst_dict = dst_dict

        self.tag_geo_land = tag_geo_land
        self.tag_folder_name = 'folder_name'
        self.tag_file_name = 'file_name'

        self.folder_name = self.src_dict[self.tag_geo_land][self.tag_folder_name]
        self.file_name = self.src_dict[self.tag_geo_land][self.tag_file_name]

        self.file_path = os.path.join(self.folder_name, self.file_name)

    # Method to read geographical datasets
    def read_data(self):

        logging.info(' ----> Read geographical file ' + self.file_name + ' ... ')
        if os.path.exists(self.file_path):
            geo_obj = get_file_raster(self.file_path)
            logging.info(' ----> Read geographical file ' + self.file_name + ' ... DONE')
        else:
            logging.error(' ==> Read geographical file ' + self.file_name + ' ... FAILED')
            raise IOError('File does not exist')
        return geo_obj
# -------------------------------------------------------------------------------------
