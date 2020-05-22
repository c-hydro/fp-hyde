import logging
import warnings
import os

import xarray as xr
import numpy as np

from osgeo import gdalconst
from copy import deepcopy

from lib_utils_geo import read_file_geo, translate_file_type, reproject_file_tiff
from lib_utils_io import create_filename_tmp, read_file_tif, write_file_tif, create_darray_2d
from lib_utils_system import make_folder


class DriverGeo:

    def __init__(self, src_dict, dest_dict, geo_var_ref='geo_ref', geo_var_other=None,
                 flag_cleaning_geo=True):

        self.src_dict = src_dict
        self.dest_dict = dest_dict

        self.geo_var_ref = geo_var_ref
        if geo_var_other is None:
            self.geo_var_other = ['geo_wilting_point', 'geo_field_capacity']
        else:
            self.geo_var_other = geo_var_other

        self.tag_folder = 'folder'
        self.tag_filename = 'filename'
        self.tag_tree = 'tree'

        self.folder_name_geo_ref = src_dict[geo_var_ref][self.tag_folder]
        self.file_name_geo_ref = src_dict[geo_var_ref][self.tag_filename]

        obj_geo_ref, obj_mask_ref, \
        self.wide_geo_ref, self.high_geo_ref, \
        self.proj_geo_ref, self.geotrans_geo_ref, self.mask_idx = read_file_geo(
            os.path.join(self.folder_name_geo_ref, self.file_name_geo_ref))

        self.obj_geo_ref = obj_geo_ref.to_dataset()
        self.obj_geo_ref[obj_mask_ref.name] = obj_mask_ref

        self.flag_cleaning_geo = flag_cleaning_geo

    def composer_geo(self):

        logging.info(' ---> Composing geographical information ... ')

        for var_geo_step in self.geo_var_other:

            logging.info(' ----> Get and reproj ' + var_geo_step + ' ... ')

            folder_src_comp = self.src_dict[var_geo_step][self.tag_folder]
            filename_src_comp = self.src_dict[var_geo_step][self.tag_filename]
            tree_src_comp = self.src_dict[var_geo_step][self.tag_tree]

            folder_dest_step = self.dest_dict[var_geo_step][self.tag_folder]
            filename_dest_step = self.dest_dict[var_geo_step][self.tag_filename]
            filepath_dest_step = os.path.join(folder_dest_step, filename_dest_step)
            make_folder(folder_dest_step)

            if self.flag_cleaning_geo:
                if os.path.exists(filepath_dest_step):
                    os.remove(filepath_dest_step)

            if not os.path.exists(filepath_dest_step):

                file_data_comp = []
                for folder_src_step, filename_src_step, tree_src_step in zip(
                        folder_src_comp, filename_src_comp, tree_src_comp):

                    filepath_src_step = os.path.join(folder_src_step, filename_src_step)

                    if filepath_src_step.endswith('.h5'):
                        if os.path.exists(filepath_src_step):

                            filename_tmp_translate_step = create_filename_tmp(prefix='tmp_smap_',
                                                                              folder=folder_src_step, suffix='.tiff')
                            fileinfo_src_step = {'prefix': 'HDF5:', 'tree': tree_src_step}
                            translate_file_type(filepath_src_step, filename_tmp_translate_step, fileinfo_src_step)

                            filename_tmp_reproj_step = create_filename_tmp(prefix='tmp_smap_',
                                                                           folder=folder_src_step, suffix='.tiff')

                            reproject_file_tiff(filename_tmp_translate_step, filename_tmp_reproj_step,
                                                self.wide_geo_ref, self.high_geo_ref,
                                                self.geotrans_geo_ref, self.proj_geo_ref)

                            file_data_reproj, file_proj_reproj, file_geotrans_reproj = read_file_tif(filename_tmp_reproj_step)
                            file_dims_reproj = file_data_reproj.shape
                            file_data_reproj_tmp = deepcopy(file_data_reproj.ravel())
                            file_data_reproj_tmp[self.mask_idx] = np.nan
                            file_data_mask = np.reshape(file_data_reproj_tmp,
                                                        [file_dims_reproj[0], file_dims_reproj[1]])

                            file_data_comp.append(file_data_mask)

                            if os.path.exists(filename_tmp_translate_step):
                                os.remove(filename_tmp_translate_step)
                                os.remove(filename_tmp_translate_step + '.aux.xml')
                            if os.path.exists(filename_tmp_reproj_step):
                                os.remove(filename_tmp_reproj_step)

                            logging.info(' ----> Get and reproj ' + var_geo_step + ' ... DONE')

                        else:
                            logging.info(' ----> Get and reproj ' + var_geo_step + ' ... FAILED')
                            logging.error(' ===> Geographical file type is not permitted!')
                            raise NotImplementedError('File type reader not implemented yet')
                    else:
                        logging.info(' ----> Get and reproj ' + var_geo_step + ' ... FAILED')
                        logging.error(' ===> Geographical file type is not permitted!')
                        raise NotImplementedError('File type reader not implemented yet')

                if var_geo_step == 'geo_wilting_point':
                    file_data_value = np.float32(file_data_comp[0])  # wp
                    file_data_value = file_data_value #* 1000
                elif var_geo_step == 'geo_field_capacity':
                    file_data_comp_1 = np.float32(file_data_comp[0]) # tfc
                    file_data_comp_2 = np.float32(file_data_comp[1]) # pr

                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        file_data_comp_1[file_data_comp_1 < 0] = np.nan
                        file_data_value = (0.001 * file_data_comp_1) / file_data_comp_2
                        file_data_value = file_data_value #* 1000
                else:
                    logging.error(' ===> Geographical variable is not allowed!')
                    raise NotImplementedError('Variable type not implemented yet')

                file_data_value = np.float32(file_data_value)

                file_data_tmp = deepcopy(file_data_value.ravel())
                file_data_tmp[self.mask_idx] = np.nan
                file_data_mask = np.reshape(file_data_tmp, [self.high_geo_ref, self.wide_geo_ref])

                write_file_tif(filepath_dest_step, file_data_mask, self.wide_geo_ref, self.high_geo_ref,
                               self.geotrans_geo_ref, self.proj_geo_ref,
                               file_format=gdalconst.GDT_Float32)

            else:
                logging.info(' ----> Get and reproj ' + var_geo_step + ' ... SKIPPED. PREVIOUSLY DONE.')

            file_dest_data, file_dest_proj, file_dest_geotrans = read_file_tif(filepath_dest_step)

            da_dest = create_darray_2d(file_dest_data,
                                       self.obj_geo_ref['west_east'].values,
                                       self.obj_geo_ref['south_north'].values, name=var_geo_step,
                                       coord_name_x='west_east', coord_name_y='south_north',
                                       dim_name_x='west_east', dim_name_y='south_north')

            self.obj_geo_ref[var_geo_step] = da_dest

        logging.info(' ---> Composing geographical information ... DONE')
