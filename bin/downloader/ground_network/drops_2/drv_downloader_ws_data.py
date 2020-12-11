# -------------------------------------------------------------------------------------
# Libraries
import logging
import os

import numpy as np
import pandas as pd
import geopandas as gpd

from shapely.geometry import Point

from bin.downloader.ground_network.drops_2.lib_utils_io import read_file_json, write_file_csv
from bin.downloader.ground_network.drops_2.lib_utils_system import fill_tags2string, make_folder
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class driver geographical data
class DriverData:

    def __init__(self, time_step, src_dict, dst_dict=None, ancillary_dict=None,
                 time_dict=None, variable_dict=None, template_dict=None,
                 tag_registry='registry', tag_datasets='datasets',
                 flag_updating_destination=True):

        self.time_step = time_step

        self.src_dict = src_dict
        self.dst_dict = dst_dict
        self.time_dict = time_dict
        self.variable_dict = variable_dict
        self.template_dict = template_dict

        self.tag_registry = tag_registry
        self.tag_dset = tag_datasets
        self.tag_folder_name = 'folder_name'
        self.tag_file_name = 'file_name'

        self.tag_file_fields = 'fields'

        self.domain_name = ancillary_dict['domain']
        self.variable_list = list(self.variable_dict.keys())

        self.time_range = self.collect_file_time()

        self.folder_name_src_registry_raw = self.src_dict[self.tag_registry][self.tag_folder_name]
        self.file_name_src_registry_raw = self.src_dict[self.tag_registry][self.tag_file_name]
        self.file_path_src_registry_obj = self.collect_file_list(self.folder_name_src_registry_raw,
                                                                 self.file_name_src_registry_raw)

        self.folder_name_src_dset_raw = self.src_dict[self.tag_dset][self.tag_folder_name]
        self.file_name_src_dset_raw = self.src_dict[self.tag_dset][self.tag_file_name]
        self.file_path_src_dset_obj = self.collect_file_list(self.folder_name_src_dset_raw,
                                                             self.file_name_src_dset_raw)

        self.folder_name_dst_dset_raw = self.dst_dict[self.tag_folder_name]
        self.file_name_dst_dset_raw = self.dst_dict[self.tag_file_name]
        self.file_path_dst_dset_obj = self.collect_file_list(self.folder_name_dst_dset_raw, self.file_name_dst_dset_raw)

        self.file_fields_dst_dset = self.dst_dict[self.tag_file_fields]

        self.flag_updating_destination = flag_updating_destination

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect time(s)
    def collect_file_time(self):

        time_period = self.time_dict["time_period"]
        time_frequency = self.time_dict["time_frequency"]
        time_rounding = self.time_dict["time_rounding"]

        time_end = self.time_step.floor(time_rounding)

        time_range = pd.date_range(end=time_end, periods=time_period, freq=time_frequency)

        return time_range
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect ancillary file
    def collect_file_list(self, folder_name_raw, file_name_raw):

        domain_name = self.domain_name

        file_name_obj = {}
        for variable_step in self.variable_list:
            variable_tag = self.variable_dict[variable_step]['tag']

            if variable_tag is not None:
                file_name_list = []
                for datetime_step in self.time_range:

                    template_values_step = {
                        'domain_name': domain_name,
                        'source_var_name': variable_tag,
                        'destination_var_name': variable_step,
                        'source_registry_datetime': datetime_step, 'source_registry_sub_path_time': datetime_step,
                        'source_datasets_datetime': datetime_step, 'source_datasets_sub_path_time': datetime_step,
                        'destination_datetime': datetime_step, 'destination_sub_path_time': datetime_step}

                    folder_name_def = fill_tags2string(
                        folder_name_raw, self.template_dict, template_values_step)
                    file_name_def = fill_tags2string(
                        file_name_raw, self.template_dict, template_values_step)
                    file_path_def = os.path.join(folder_name_def, file_name_def)

                    file_name_list.append(file_path_def)

                file_name_obj[variable_step] = file_name_list

        return file_name_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to download datasets
    def download_data(self):
        pass
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize datasets
    def organize_data(self):

        logging.info(' ----> Organize datasets ... ')
        time_range = self.time_range

        for variable_step in self.variable_list:

            # DEBUG
            # variable_step = 'air_temperature'
            # variable_step = 'relative_humidity'
            # variable_step = 'wind_direction'

            logging.info(' -----> Variable ' + variable_step + ' ... ')

            variable_tag = self.variable_dict[variable_step]['tag']
            variable_units = self.variable_dict[variable_step]['units']
            variable_scale_factor = self.variable_dict[variable_step]['scale_factor']

            if variable_step in list(self.file_path_src_dset_obj.keys()):

                file_path_src_registry_list = self.file_path_src_registry_obj[variable_step]
                file_path_src_dset_list = self.file_path_src_dset_obj[variable_step]
                file_path_dst_dset_list = self.file_path_dst_dset_obj[variable_step]

                file_path_list = zip(file_path_src_registry_list, file_path_src_dset_list, file_path_dst_dset_list)

                file_path_prev_dset = None
                for time_step, file_path_step in zip(time_range, file_path_list):

                    logging.info(' ------> TimeStep ' + str(time_step) + ' ... ')

                    if file_path_step.__len__() == 3:
                        file_path_src_registry = file_path_step[0]
                        file_path_src_dset = file_path_step[1]
                        file_path_dst_dset = file_path_step[2]

                    elif file_path_step.__len__() == 2:
                        file_path_src_dset = file_path_step[0]
                        file_path_src_registry = None
                        file_path_dst_dset = file_path_step[1]
                    else:
                        raise IOError

                    if self.flag_updating_destination:
                        if os.path.exists(file_path_dst_dset):
                            os.remove(file_path_dst_dset)

                    if not os.path.exists(file_path_dst_dset):

                        gdf_registry = None
                        if (file_path_src_registry is not None) and file_path_src_registry.endswith('.json'):
                            if os.path.exists(file_path_src_registry):
                                gdf_registry = self.get_file_registry(file_path_src_registry)

                        if file_path_src_dset.endswith('.json'):
                            if os.path.exists(file_path_src_dset):

                                if (file_path_prev_dset is None) or (file_path_prev_dset != file_path_src_dset):
                                    df_dset = self.get_file_dset(file_path_src_dset)
                                    file_path_prev_dset = file_path_src_dset
                            else:
                                df_dset = None
                        else:
                            df_dset = None

                        df_dset_select = None
                        if df_dset is not None:
                            datetime_step = pd.DatetimeIndex([time_step])

                            datetime_value = datetime_step[0]

                            df_index = df_dset.index
                            df_index = df_index.tz_localize(None)
                            if datetime_value in list(df_index):
                                df_dset_select = df_dset.loc[datetime_value]
                            else:
                                df_dset_select = None
                                logging.warning(' ===> Datasets are undefined for time ' +
                                                datetime_step[0].strftime('%y-%m-%d %H:%M'))
                        if df_dset_select is not None:
                            dict_dset_select = df_dset_select.to_dict()
                            dict_registry = gdf_registry.to_dict()
                            dict_geometry = dict_registry['geometry']
                            dict_name = dict_registry['name']
                            dict_mu = dict_registry['mu']

                            point_name_list = []
                            point_code_list = []
                            point_x_list = []
                            point_y_list = []
                            point_z_list = []
                            point_value_list = []
                            point_time_start_list = []
                            point_time_end_list = []
                            point_unit_list = []
                            for point_code, point_ws in dict_dset_select.items():
                                if point_code in list(dict_geometry.keys()):

                                    point_time_range = pd.date_range(end=time_step, periods=2, freq='H')

                                    point_geometry = dict_geometry[point_code]
                                    point_name = dict_name[point_code]
                                    point_unit = dict_mu[point_code]
                                    point_x = point_geometry.x
                                    point_y = point_geometry.y

                                    if isinstance(point_ws, dict):
                                        # point_time = list(point_ws.keys())[0]
                                        point_value = list(point_ws.values())[0]
                                    else:
                                        point_value = point_ws

                                    point_unit = point_unit.replace('°', '')

                                    if not variable_units == point_unit:
                                        logging.info(' ------> Unit mismatching for sensor ' + point_code)
                                        logging.warning(
                                            ' ===> Mismatching between expected unit ' + variable_units +
                                            ' and found unit ' + point_unit)
                                    elif variable_units == point_unit:
                                        if np.isnan(point_value):
                                            point_value = -9999.0
                                        else:
                                            point_value = point_value * variable_scale_factor

                                        point_name_list.append(point_name.replace(' ', '_'))
                                        point_code_list.append(point_code)
                                        point_x_list.append(point_x)
                                        point_y_list.append(point_y)
                                        point_z_list.append(-9999)
                                        point_value_list.append(point_value)
                                        point_unit_list.append(variable_units)

                                        point_time_start_list.append(point_time_range[0])
                                        point_time_end_list.append(point_time_range[1])

                            # Create dataframe
                            point_df = pd.DataFrame(
                                {'longitude': point_x_list, 'latitude': point_y_list, 'altitude': point_z_list,
                                 'data': point_value_list, 'name': point_name_list, 'code': point_code_list,
                                 'time_start': point_time_start_list, 'time_end': point_time_end_list,
                                 'units': point_unit_list},
                                columns=self.file_fields_dst_dset)

                            # Define dataframe dtype(s)
                            point_df["longitude"] = pd.to_numeric(point_df["longitude"])
                            point_df["latitude"] = pd.to_numeric(point_df["latitude"])
                            point_df["altitude"] = pd.to_numeric(point_df["altitude"])
                            point_df["data"] = pd.to_numeric(point_df["data"])
                            point_df["code"] = point_df["code"]
                            point_df["time_start"] = point_df["time_start"]
                            point_df["time_end"] = point_df["time_end"]

                            folder_name_dst_dset, file_name_dst_dset = os.path.split(file_path_dst_dset)
                            make_folder(folder_name_dst_dset)

                            write_file_csv(file_path_dst_dset, point_df)

                            logging.info(' ------> TimeStep ' + str(time_step) + ' ... DONE')

                        else:

                            logging.info(' ------> TimeStep ' + str(time_step) + ' ... SKIPPED. Datasets is undefined')

                    else:

                        logging.info(' ------> TimeStep ' + str(time_step) + ' ... PREVIOUSLY DONE')

                logging.info(' -----> Variable ' + variable_step + ' ... DONE')

            else:

                logging.info(' -----> Variable ' + variable_step + ' ... SKIPPED. Datasets is undefined')

        logging.info(' ----> Organize datasets ... DONE')

    @staticmethod
    def get_file_registry(file_name,
                          sensor_id_key=None, sensor_name_key=None, sensor_mu_key=None,
                          sensor_lon_key=None, sensor_lat_key=None):

        if sensor_id_key is None:
            sensor_id_key = ['id']
        if sensor_lat_key is None:
            sensor_lat_key = ['lat']
        if sensor_lon_key is None:
            sensor_lon_key = ['lon', 'lng']
        if sensor_name_key is None:
            sensor_name_key = ['stationName', 'name']
        if sensor_mu_key is None:
            sensor_mu_key = ['sensorMU', 'mu']

        file_handle = read_file_json(file_name)
        file_keys = list(file_handle[0].keys())

        sensor_id_select = [key_step for key_step in sensor_id_key if key_step in file_keys][0]
        sensor_lat_select = [key_step for key_step in sensor_lat_key if key_step in file_keys][0]
        sensor_lon_select = [key_step for key_step in sensor_lon_key if key_step in file_keys][0]
        sensor_name_select = [key_step for key_step in sensor_name_key if key_step in file_keys][0]
        sensor_mu_select = [key_step for key_step in sensor_mu_key if key_step in file_keys][0]

        index = [s[sensor_id_select] for s in file_handle]
        data = [(s[sensor_name_select], s[sensor_mu_select]) for s in file_handle]
        geometry = [Point((s[sensor_lon_select], s[sensor_lat_select])) for s in file_handle]
        df_registry = gpd.GeoDataFrame(data, index=index, columns=['name', 'mu'], geometry=geometry)
        df_registry.index.name = 'id'

        return df_registry.copy()

    @staticmethod
    def get_file_dset(file_name):

        file_handle = read_file_json(file_name)

        count_tot = 0
        count_failed = 0

        df_dset = pd.DataFrame()
        for file_id, file_row in enumerate(file_handle):

            count_tot += 1

            column = pd.Series(file_row['values'], index=file_row['timeline'])
            column.index = pd.to_datetime(column.index)
            try:
                df_dset[file_row['sensorId']] = column
            except Exception as exc:
                count_failed += 1
                # logging.warning(' ===> Errors in parsing datasets for sensor ' + file_row['sensorId'])
        df_dset.index = pd.to_datetime(df_dset.index)

        logging.info(' ------> Datasets N: ' + str(count_tot) + ' Failed: ' + str(count_failed))

        return df_dset.copy()

# -------------------------------------------------------------------------------------
