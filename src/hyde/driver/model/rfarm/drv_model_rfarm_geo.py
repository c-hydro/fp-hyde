"""
Class Features

Name:          drv_model_rfarm_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190729'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import os

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_name
from src.hyde.algorithm.geo.model.rfarm.lib_rfarm_geo import read_file_raster
from src.hyde.algorithm.io.model.rfarm.lib_rfarm_io_generic import read_obj, write_obj
from src.hyde.algorithm.utils.rfarm.lib_rfarm_generic import make_folder

# Log
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Class to compute geographical data
class DataGeo:

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, src_dict,
                 tag_folder_name='folder', tag_file_name='filename',
                 tag_terrain_data='terrain_data', tag_alert_area_data='alert_area_data',
                 tag_ancillary_data='grid_data',
                 cleaning_static_data=True):

        # -------------------------------------------------------------------------------------
        # Get path(s) and filename(s)
        self.src_dict = src_dict

        self.tag_folder_name = tag_folder_name
        self.tag_file_name = tag_file_name

        self.tag_terrain_data = tag_terrain_data
        self.tag_alert_area_data = tag_alert_area_data
        self.tag_ancillary_data = tag_ancillary_data

        self.folder_name_terrain = src_dict[self.tag_terrain_data][self.tag_folder_name]
        self.file_name_terrain = src_dict[self.tag_terrain_data][self.tag_file_name]
        self.file_path_terrain = os.path.join(self.folder_name_terrain, self.file_name_terrain)

        if self.tag_alert_area_data in list(src_dict.keys()):
            self.folder_name_alert_area = src_dict[self.tag_alert_area_data][self.tag_folder_name]
            self.file_name_alert_area = src_dict[self.tag_alert_area_data][self.tag_file_name]
            self.file_path_alert_area = os.path.join(self.folder_name_alert_area, self.file_name_alert_area)
        else:
            self.folder_name_alert_area = None
            self.file_name_alert_area = None
            self.file_path_alert_area = None

        self.folder_name_ancillary = src_dict[self.tag_ancillary_data][self.tag_folder_name]
        self.file_name_ancillary = src_dict[self.tag_ancillary_data][self.tag_file_name]
        self.file_path_ancillary = os.path.join(self.folder_name_ancillary, self.file_name_ancillary)

        self.cleaning_static_data = cleaning_static_data

        if self.cleaning_static_data:
            if os.path.exists(self.file_path_ancillary):
                os.remove(self.file_path_ancillary)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compose geographical data
    def compose(self):

        log_stream.info(' ---> Organize Geo ... ')

        geo_collections = {}
        if not os.path.exists(self.file_path_ancillary):

            log_stream.info(' ----> Terrain datasets ... ')
            if os.path.exists(self.file_path_terrain):
                terrain_obj = read_file_raster(self.file_path_terrain)
                log_stream.info(' ----> Terrain datasets ... DOME')
            else:
                log_stream.error(' ----> Terrain datasets ... FAILED! File not found.')
                raise FileNotFoundError('File ' + self.file_path_terrain + ' not found')

            log_stream.info(' ----> Alert area datasets ... ')
            if (self.file_path_alert_area is not None) and (os.path.exists(self.file_path_alert_area)):
                alert_area_obj = read_file_raster(self.file_path_alert_area)
                log_stream.info(' ----> Alert area datasets ... DOME')
            else:
                log_stream.info(' ----> Alert area datasets ... SKIPPED! File not defined or not found.')
                alert_area_obj = None

            # Create geo collections
            geo_collections[self.tag_terrain_data] = terrain_obj
            geo_collections[self.tag_alert_area_data] = alert_area_obj

            # Save geo collections
            folder_name, file_name = os.path.split(self.file_path_terrain)
            make_folder(folder_name)
            write_obj(self.file_path_ancillary, geo_collections)

        else:
            # Read geo collections
            geo_collections = read_obj(self.file_path_ancillary)

        log_stream.info(' ---> Organize Geo ... DONE')

        return geo_collections

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
