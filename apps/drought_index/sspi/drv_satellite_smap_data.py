
import logging
import warnings
import os
import re

import scipy.stats as stats
import numpy as np
import pandas as pd

from lib_utils_io import read_file_tif, write_file_tif, create_darray_3d
from lib_utils_system import fill_tags2string, convert_list2dict, make_folder


class DriverData:

    def __init__(self, time_run, src_dict, dest_dict, stats_dict,
                 template_tags, time_frequency='3H', time_offset=0,
                 data_geo=None, data_proj=None, data_transform=None, file_ancillary='nrt_db.pickle',
                 flag_cleaning_result=False):

        self.time_run = pd.Timestamp(time_run)

        self.tag_folder = 'folder'
        self.tag_filename = 'filename'

        self.folder_name_src = src_dict[self.tag_folder]
        self.file_name_src = src_dict[self.tag_filename]

        self.folder_name_dest = dest_dict[self.tag_folder]
        self.file_name_dest = dest_dict[self.tag_filename]

        self.folder_name_stats = stats_dict[self.tag_folder]
        self.file_name_stats = stats_dict[self.tag_filename]

        self.time_frequency = time_frequency
        self.time_offset = time_offset
        self.time_regexp = r'\d{4}\d{2}\d{2}\w\d{2}\d{2}'

        self.template_tags = template_tags
        self.geo_values_tag = 'geo_values'
        self.geo_mask_tag = 'geo_mask'
        self.geo_field_capacity_tag = 'geo_field_capacity'
        self.geo_wilting_point_tag = 'geo_wilting_point'

        self.gamma_k_tag = 'k'
        self.gamma_theta_tag = 'theta'
        self.gamma_count_ratio_tag = 'count_ratio'
        self.drought_index_tag = 'sspi'

        self.month_n_ref = [1, 2, 3, 6]
        self.month_n_tag = 'month_{:}'

        self.template_tags = template_tags

        self.time_run, n_steps, hour_steps, mins_steps = self.select_time_step()

        self.time_period, self.time_first, self.time_last, self.time_save = self.select_time_period(n_steps, hour_steps,
                                                                                                    mins_steps)

        self.n_threshold = 0.9
        self.file_src = self.search_filename()

        for file_month, file_list in self.file_src.items():
            if not file_list:
                logging.error(' ==> File list of ' + str(file_month) + ' for collecting data is empty')
                raise IOError('Check folder and filename used for searching file(s)')

        self.data_geo = data_geo
        self.data_proj = data_proj
        self.data_transform = data_transform

        self.file_ancillary = file_ancillary
        self.flag_cleaning_result = flag_cleaning_result

    def select_time_step(self, hour_ref=1, mins_ref=30):

        time_run = self.time_run

        time_stamp_from = time_run.replace(hour=hour_ref, minute=mins_ref)
        time_stamp_to = pd.date_range(start=time_stamp_from, periods=2, freq='1D')[1].floor('D')
        time_steps = pd.date_range(start=time_stamp_from, end=time_stamp_to, closed='left', freq=self.time_frequency)

        hour_steps = time_steps.hour
        mins_steps = time_steps.minute
        n_steps = hour_steps.__len__()

        hour_run = time_run.hour

        hour_diff = hour_steps - hour_run
        hour_idx = np.where(hour_diff < 0, hour_diff, -np.inf).argmax()
        hour_select = hour_steps[hour_idx]
        mins_select = mins_steps[hour_idx]

        time_run = time_run.replace(hour=hour_select, minute=mins_select)

        return time_run, n_steps, hour_steps, mins_steps

    def select_time_period(self, time_n, hour_steps, mins_steps):

        time_period = time_n * self.time_offset
        if time_period > 0:
            time_check = pd.date_range(end=self.time_run, periods=time_period, freq=self.time_frequency)
            month_from = time_check[0].month
            month_to = time_check[-1].month
            month_run = self.time_run.month
        else:
            time_check = self.time_run
            month_from = time_check.month
            month_to = time_check.month
            month_run = self.time_run.month

        if month_from != month_run:
            month_select = month_from
            days_select = time_check[0].days_in_month
            year_select = time_check[0].year
        else:
            month_select = month_run
            days_select = self.time_run.days_in_month
            year_select = self.time_run.year

        if month_from == month_to:
            month_select = month_run
            days_select = self.time_run.day
            year_select = self.time_run.year
            hour_select = self.time_run.hour
            mins_select = self.time_run.minute
        else:
            hour_select = hour_steps[-1]
            mins_select = mins_steps[-1]

        time_to = pd.Timestamp(year=year_select, month=month_select,
                               day=days_select, hour=hour_select, minute=mins_select)
        time_last = time_to

        time_first = None
        time_range_dict = {}
        for month_ref in self.month_n_ref:

            time_from = time_to.floor('d') - month_ref * pd.offsets.MonthBegin(1)
            time_from = time_from.replace(hour=hour_steps[0], minute=mins_steps[0])

            if time_first is None:
                time_first = time_from
            else:
                if time_from < time_first:
                    time_first = time_from

            time_range = pd.date_range(start=time_from, end=time_to, freq=self.time_frequency)

            time_range_dict[self.month_n_tag.format(month_ref)] = time_range

        time_save = time_to

        return time_range_dict, time_first, time_last, time_save

    def search_filename(self):

        file_name_raw = self.file_name_src
        folder_name_raw = self.folder_name_src
        template_tags = self.template_tags
        time_period = self.time_period

        file_list_dict = {}
        for month_step, time_range in time_period.items():
            file_list_def = []
            for time_step in time_range:
                template_values = {"source_sub_path_time": time_step,
                                   "source_datetime": time_step}

                folder_name_def = fill_tags2string(folder_name_raw, template_tags, template_values)
                file_name_def = fill_tags2string(file_name_raw, template_tags, template_values)
                path_name_def = os.path.join(folder_name_def, file_name_def)

                if os.path.exists(path_name_def):
                    file_list_def.append(path_name_def)

            file_list_dict[month_step] = file_list_def

            n_found = file_list_def.__len__()
            n_expected = time_range.__len__()
            n_ratio = float(n_found) / float(n_expected)

            logging.info(' ---> Period: ' + str(time_range[0]) + ' -- ' + str(time_range[-1]))
            logging.info(' ---> File(s) available: ' + str(n_ratio * 100) + ' % ')
            if n_ratio < self.n_threshold:
                logging.warning(' ---> File(s) available are less then threshold of ' +
                                str(self.n_threshold * 100) + ' % ')

        return file_list_dict

    def reader_data(self):

        logging.info(' ---> Reading data ... ')
        data_geo = self.data_geo[self.geo_values_tag].values
        mask_geo = np.float32(self.data_geo[self.geo_mask_tag].values)

        latitude_geo = self.data_geo['south_north'].values
        longitude_geo = self.data_geo['west_east'].values

        mask_geo[mask_geo == 0] = np.nan
        if self.file_src:

            ws_obj = {}
            for file_month, file_list in self.file_src.items():
                data_obj = {}
                file_time_list = []
                file_data_tmp = np.zeros(shape=[data_geo.shape[0], data_geo.shape[1], file_list.__len__()])
                file_data_tmp[:, :, :] = np.nan
                for file_id, file_path_step in enumerate(file_list):

                    folder_name_step, file_name_step = os.path.split(file_path_step)

                    if os.path.exists(file_path_step):
                        try:
                            file_data_step, file_proj_step, file_geotrans_step = read_file_tif(file_path_step)
                            file_data_tmp[:, :, file_id] = file_data_step * mask_geo

                            time_match_step = re.search(self.time_regexp, file_name_step)
                            time_str_step = time_match_step.group()
                            file_time_step = pd.Timestamp(time_str_step)

                            file_time_list.append(file_time_step)

                        except IOError as io_exc:
                            logging.warning(' ===> Open ' + file_name_step + ' FAILED. Detect error ' + str(io_exc))
                    else:
                        logging.warning(' ===> Open ' + file_name_step + ' FAILED. File does not exist')

                file_year_avg = pd.DatetimeIndex(file_time_list).year.values[-1]
                file_month_avg = pd.DatetimeIndex(file_time_list).month.values[-1]
                file_time_avg = pd.Timestamp(year=file_year_avg, month=file_month_avg, day=1).strftime('%Y-%m')

                file_time_idx_tmp = pd.DatetimeIndex(file_time_list)
                da_tmp = create_darray_3d(
                    file_data_tmp, file_time_idx_tmp, longitude_geo, latitude_geo,
                    geo_1d=True, coord_name_x='west_east', coord_name_y='south_north', coord_name_time='time',
                    dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time')

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    da_mean = da_tmp.resample(time="1D").mean()
                    data_obj[file_time_avg] = np.nanmean(da_mean.values, axis=2)

                ws_obj[file_month] = data_obj

            logging.info(' ---> Reading data ... DONE')

        else:
            logging.info(' ---> Reading data ... FAILED')
            logging.error(' ===> Reader data skipped. Selected file list is empty')
            raise IOError('Empty data list')

        return ws_obj

    def composer_data(self, ws_obj=None):

        logging.info(' ---> Computing drought index ... ')

        folder_name_stats_raw = self.folder_name_stats
        file_name_stats_raw = self.file_name_stats

        geo_mask = self.data_geo[self.geo_mask_tag].values
        geo_fc = self.data_geo[self.geo_field_capacity_tag].values
        geo_wp = self.data_geo[self.geo_wilting_point_tag].values

        file_stats_vars = [self.gamma_k_tag, self.gamma_theta_tag, self.gamma_count_ratio_tag]

        if ws_obj is not None:
            time_obj = {}
            analysis_obj = {}
            for month_n_id in self.month_n_ref:

                time_str_ref = list(ws_obj[self.month_n_tag.format(month_n_id)].keys())[0]
                time_stamp_ref = pd.Timestamp(time_str_ref)
                month_ref = time_stamp_ref.month

                values_ref = list(ws_obj[self.month_n_tag.format(month_n_id)].values())[0]
                values_ref = np.float32(values_ref)

                month_n_id_str = '{:02d}'.format(month_n_id)
                month_ref_str = '{:02d}'.format(month_ref)

                template_values = {"month_reference": month_ref_str, "month_period": month_n_id_str}

                folder_name_stats_def = fill_tags2string(folder_name_stats_raw, self.template_tags, template_values)
                file_name_stats_def = fill_tags2string(file_name_stats_raw, self.template_tags, template_values)
                file_path_stats_def = os.path.join(folder_name_stats_def, file_name_stats_def)

                if os.path.exists(file_path_stats_def):
                    file_data_step, file_proj_step, file_geotrans_step = read_file_tif(file_path_stats_def)
                else:
                    logging.error(' ==> File statistics ' + file_name_stats_def + ' does not exist')
                    raise IOError('Check folder and filename used for statistics')

                stats_dict = convert_list2dict(file_stats_vars, file_data_step)
                gamma_k = stats_dict[self.gamma_k_tag]
                gamma_theta = stats_dict[self.gamma_theta_tag]
                gamma_count_ratio = stats_dict[self.gamma_count_ratio_tag]

                # Pb = (1 - Spo) / 2 + Spo. * cdf('Gamma', squeeze(SM(:,:, i)), Sthe, Skap);
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    values_p = (1 - gamma_count_ratio) / 2 + gamma_count_ratio * stats.gamma.cdf(
                        values_ref, a=gamma_k, scale=gamma_theta)

                    values_p[values_p == 0] = 0.0000001
                    values_p[values_p == 1] = 0.9999999
                    values_norm = stats.norm.ppf(values_p, loc=0, scale=1)

                    values_norm[gamma_count_ratio == 0] = np.nan
                    values_norm = values_norm * geo_mask

                    time_obj[self.month_n_tag.format(month_n_id)] = time_stamp_ref
                    analysis_obj[self.month_n_tag.format(month_n_id)] = values_norm

            logging.info(' ---> Computing drought index ... DONE')
        else:
            logging.info(' ---> Computing drought index ... DONE')
            logging.error(' ===> Composer data skipped. Selected file list is empty')
            raise IOError('Empty data list')

        return time_obj, analysis_obj

    def writer_data(self, time_obj, analysis_obj):

        logging.info(' ---> Writing results ... ')

        time_dump = self.time_save

        folder_name_dest_raw = self.folder_name_dest
        file_name_dest_raw = self.file_name_dest

        data_high, data_wide = self.data_geo[self.geo_values_tag].values.shape
        var_name = self.drought_index_tag

        month_data = None
        for month_ref, time_data, var_data in zip(self.month_n_ref, time_obj.values(), analysis_obj.values()):

            if month_data is None:
                month_data = time_data.month

            month_data_str = '{:02d}'.format(month_data)
            month_ref_str = '{:02d}'.format(month_ref)

            metadata_list = [{'description_field': var_name}]
            analysis_list = [var_data]

            template_values = {"month_reference": month_data_str, "month_period": month_ref_str,
                               "outcome_sub_path_time": time_dump, "outcome_datetime": time_dump}

            folder_name_dest_def = fill_tags2string(folder_name_dest_raw, self.template_tags, template_values)
            file_name_dest_def = fill_tags2string(file_name_dest_raw, self.template_tags, template_values)
            file_path_dest_def = os.path.join(folder_name_dest_def, file_name_dest_def)
            make_folder(folder_name_dest_def)

            logging.info(' ----> Dumping filename ' + file_name_dest_def + ' ... ')

            if self.flag_cleaning_result:
                if os.path.exists(file_path_dest_def):
                    os.remove(file_path_dest_def)

            if not os.path.exists(file_path_dest_def):
                write_file_tif(file_path_dest_def, analysis_list,
                               data_wide, data_high, self.data_transform, self.data_proj,
                               file_metadata=metadata_list)

                logging.info(' ----> Dumping filename ' + file_name_dest_def + ' ... DONE')
            else:
                logging.info(' ----> Dumping filename ' + file_name_dest_def + ' ... PREVIOUSLY DONE')

        logging.info(' ---> Writing results ... DONE')


