import logging
import warnings
import os
import re

import numpy as np
import pandas as pd

from copy import deepcopy

from lib_utils_io import read_file_tif, read_obj, write_obj, write_file_tif
from lib_utils_system import fill_tags2string, make_folder

from lib_utils_statistics import filter_data, compute_moments_data_first_order, compute_norm_data


class DriverStatistics:

    def __init__(self, time_run, src_dict, dest_dict, ancillary_dict, template_tags, time_frequency='3H', time_offset=0,
                 data_geo=None, data_proj=None, data_transform=None,
                 flag_cleaning_statistics=True):

        self.time_run = pd.Timestamp(time_run)

        self.tag_folder = 'folder'
        self.tag_filename = 'filename'

        self.folder_name_src = src_dict[self.tag_folder]
        self.file_name_src = src_dict[self.tag_filename]

        self.folder_name_dest = dest_dict[self.tag_folder]
        self.file_name_dest = dest_dict[self.tag_filename]

        self.folder_name_ancillary = ancillary_dict[self.tag_folder]
        self.file_name_ancillary = ancillary_dict[self.tag_filename]

        self.time_frequency = time_frequency
        self.time_offset = time_offset
        self.time_regexp = r'\d{4}\d{2}\d{2}\w\d{2}\d{2}'

        self.template_tags = template_tags
        self.geo_values_tag = 'geo_values'
        self.geo_mask_tag = 'geo_mask'
        self.geo_field_capacity_tag = 'geo_field_capacity'
        self.geo_wilting_point_tag = 'geo_wilting_point'

        self.stdev_tag = 'std'
        self.mean_tag = 'mean'
        self.drought_index_tag = 'swdi'

        self.month_n_ref = [1, 2, 3, 6]

        self.file_prefix_src, self.file_suffix_src = self.define_filepart()
        self.file_list_src = self.search_filename()

        if not self.file_list_src:
            logging.error(' ==> File list for statistics is empty')
            raise IOError('Check folder and filename used for searching file(s)')

        self.time_idx_expected, self.time_idx_start, self.time_idx_end = self.search_filetime()

        self.data_geo = data_geo
        self.data_proj = data_proj
        self.data_transform = data_transform

        self.file_ancillary = os.path.join(self.folder_name_ancillary, self.file_name_ancillary)
        make_folder(self.folder_name_ancillary)

        self.flag_cleaning_statistics = flag_cleaning_statistics

        if self.flag_cleaning_statistics:
            if os.path.exists(self.file_ancillary):
                os.remove(self.file_ancillary)

    def define_filepart(self, tag_null='*'):

        template_file_name = self.file_name_src
        template_values = {"statistics_datetime": tag_null}

        file_name_tmp = fill_tags2string(template_file_name, self.template_tags, template_values)

        file_prefix_src = file_name_tmp.split(tag_null)[0]
        file_suffix_src = file_name_tmp.split(tag_null)[-1]

        return file_prefix_src, file_suffix_src

    def search_filename(self, ):

        file_path_list = []
        for dirpath, dirnames, filenames in os.walk(self.folder_name_src):
            for filename in [f for f in filenames if f.startswith(
                    self.file_prefix_src) and f.endswith(self.file_suffix_src)]:
                file_path = os.path.join(dirpath, filename)
                file_path_list.append(file_path)
        file_path_list_src = sorted(file_path_list)
        return file_path_list_src

    def search_filetime(self):

        time_stamp_found = []
        for file_name in self.file_list_src:
            match_time = re.search(self.time_regexp, file_name)
            time_str = match_time.group()
            time_stamp = pd.Timestamp(time_str)
            time_stamp_found.append(time_stamp)
        time_idx_found = pd.DatetimeIndex(time_stamp_found)

        time_start = time_stamp_found[0]
        time_end = time_stamp_found[-1]

        time_idx_expected = pd.date_range(start=time_start, end=time_end, freq=self.time_frequency)
        time_idx_missed = time_idx_expected.difference(time_idx_found)
        if time_idx_missed.__len__() > 0:
            file_n_missed = time_idx_missed.__len__()
            file_n_expected = time_idx_expected.__len__()
            logging.warning(' ===> {0}/{1} files are unavailable'.format(file_n_missed, file_n_expected))
            logging.warning(' ===> {0} time(s)'.format(list(time_idx_missed.values)))

        time_idx_start = pd.date_range(start=time_idx_expected[0], end=time_idx_expected[-1], freq='MS')
        time_stamp_end = []
        for time_idx_step in time_idx_start:
            time_idx_tmp = pd.date_range(start=time_idx_step, periods=time_idx_step.days_in_month * 8, freq='3H')[-1]
            time_stamp_end.append(time_idx_tmp)
        time_idx_end = pd.DatetimeIndex(time_stamp_end)

        return time_idx_expected, time_idx_start, time_idx_end

    def reader_data(self):

        logging.info(' ---> Reading data ... ')
        data_geo = self.data_geo[self.geo_values_tag]
        mask_geo = self.data_geo[self.geo_mask_tag]

        if not os.path.exists(self.file_ancillary):

            ws_data = {}
            ws_counter = {}
            for file_time_step_start, file_time_step_end in zip(self.time_idx_start, self.time_idx_end):

                file_loc_step_start = self.time_idx_expected.get_loc(file_time_step_start)
                file_loc_step_end = self.time_idx_expected.get_loc(file_time_step_end)
                file_name_step_list = self.file_list_src[file_loc_step_start: file_loc_step_end]

                file_time_key = file_time_step_start.strftime('%Y-%m')

                logging.info(' ----> Analyze period ' + file_time_key + ' ... ')

                file_time_n = file_name_step_list.__len__()

                file_sample_tmp = np.ones(shape=[data_geo.shape[0], data_geo.shape[1]])
                file_data_tmp = np.zeros(shape=[data_geo.shape[0], data_geo.shape[1], file_time_n])
                file_count = 0
                for file_id, file_name_step in enumerate(file_name_step_list):

                    if os.path.exists(file_name_step):
                        try:
                            file_data_step, file_proj_step, file_geotrans_step = read_file_tif(file_name_step)
                            file_data_tmp[:, :, file_id] = file_data_step * mask_geo
                            file_count += 1
                        except IOError as io_exc:
                            logging.warning(' ===> Open ' + file_name_step + ' FAILED. Detect error ' + str(io_exc))
                    else:
                        logging.warning(' ===> Open ' + file_name_step + ' FAILED. File does not exist')

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")

                    if file_data_tmp.shape[2] > 0:
                        value_max = np.nanmax(file_data_tmp)
                        value_min = np.nanmin(file_data_tmp)
                    else:
                        value_max = np.nan
                        value_min = np.nan
                        logging.warning(' ===> Analyze period ' + file_time_key + ' is empty')
                    logging.info(' ----> Value MIN: ' + str(value_min) + '  Value MAX: ' + str(value_max))

                    ws_data[file_time_key] = np.nanmean(file_data_tmp, axis=2)
                    ws_counter[file_time_key] = file_sample_tmp * file_count

                logging.info(' ----> Analyze period ' + file_time_key + ' ... DONE')

            ws_counter_tmp = deepcopy(ws_counter)
            for ws_key, ws_values in ws_counter_tmp.items():
                if ws_values.max() == 0.0:
                    ws_counter.pop(ws_key)
                    ws_data.pop(ws_key)
                    logging.warning(' ===> Analyze period ' + ws_key + ' has been removed from datasets')

            data_obj = {'data': ws_data}

            write_obj(self.file_ancillary, data_obj)

        else:

            data_obj = read_obj(self.file_ancillary)
            ws_data = data_obj['data']

        logging.info(' ---> Reading data ... DONE')

        return ws_data

    def composer_data(self, ws_data):

        logging.info(' ---> Computing statistics ... ')

        if os.path.exists(self.file_ancillary):
            data_obj = read_obj(self.file_ancillary)
            if 'moments' not in list(data_obj.keys()):

                geo_mask = self.data_geo[self.geo_mask_tag].values
                geo_fc = self.data_geo[self.geo_field_capacity_tag].values
                geo_wp = self.data_geo[self.geo_wilting_point_tag].values

                ws_filter = filter_data(ws_data, geo_fc, geo_wp, index_name=self.drought_index_tag)
                if self.drought_index_tag == 'swdi':
                    ws_moments = compute_moments_data_first_order(ws_filter,
                                                                  tag_mean=self.mean_tag, tag_stdev=self.stdev_tag)
                    ws_norm = compute_norm_data(ws_filter, ws_moments, geo_mask)
                else:
                    logging.error(' ===> Statistical moments for index type are not available')
                    raise IOError('Statistical moments not implemented yet')

                data_obj['filter'] = ws_filter
                data_obj['moments'] = ws_moments
                data_obj['norm'] = ws_norm

                if os.path.exists(self.file_ancillary):
                    os.remove(self.file_ancillary)

                write_obj(self.file_ancillary, data_obj)
                logging.info(' ---> Computing statistics ... DONE')
            else:
                ws_moments = data_obj['moments']
                logging.info(' ---> Computing statistics ... PREVIOUSLY DONE')
        else:
            logging.info(' ---> Computing statistics ... FAILED')
            logging.error(' ===> File ancillary for statistics part is unavailable')
            raise IOError('File does not exists')

        return ws_moments

    def writer_data(self, ws_moments):

        logging.info(' ---> Writing results ... ')

        month_n_ref = self.month_n_ref
        folder_name_dest_raw = self.folder_name_dest
        file_name_dest_raw = self.file_name_dest

        data_vars = [self.mean_tag, self.stdev_tag]
        data_high, data_wide = self.data_geo[self.geo_values_tag].values.shape

        months = list(range(1, 13))
        for ref_month_id, (ref_month_key, ref_dataset) in zip(month_n_ref, ws_moments.items()):
            for step_month_id in months:

                dataset_list = []
                metadata_list = []
                for var_step in data_vars:
                    dataset_tmp = ref_dataset[var_step][step_month_id]
                    dataset_list.append(dataset_tmp)
                    metadata_list.append({'description_field': var_step})

                step_month_id_str = '{:02d}'.format(step_month_id)
                ref_month_id_str = '{:02d}'.format(ref_month_id)

                template_values = {"month_reference": step_month_id_str, "month_period": ref_month_id_str}

                folder_name_dest_def = fill_tags2string(folder_name_dest_raw, self.template_tags, template_values)
                file_name_dest_def = fill_tags2string(file_name_dest_raw, self.template_tags, template_values)
                file_path_dest_def = os.path.join(folder_name_dest_def, file_name_dest_def)
                make_folder(folder_name_dest_def)

                logging.info(' ----> Dumping filename ' + file_name_dest_def + ' ... ')

                if self.flag_cleaning_statistics:
                    if os.path.exists(file_path_dest_def):
                        os.remove(file_path_dest_def)

                if not os.path.exists(file_path_dest_def):
                    write_file_tif(file_path_dest_def, dataset_list,
                                   data_wide, data_high, self.data_transform, self.data_proj,
                                   file_metadata=metadata_list)
                    logging.info(' ----> Dumping filename ' + file_name_dest_def + ' ... DONE')
                else:
                    logging.info(' ----> Dumping filename ' + file_name_dest_def + ' ... PREVIOUSLY DONE')

        logging.info(' ---> Writing results ... DONE')
