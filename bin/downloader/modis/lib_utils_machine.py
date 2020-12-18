# -------------------------------------------------------------------------------------
# Libraries
import logging
import os
import netrc

from bin.downloader.modis.lib_utils_system import remove_url
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define machine script downloader
def define_machine_script_downloader(folder_name_download, file_name_download,
                                     folder_name_src, file_name_src, url_address_src,
                                     machine_address, machine_user, machine_password):

    path_address_src = remove_url(url_address_src)

    # Define script row by row
    file_lines = dict()
    file_lines[0] = str('#!/bin/bash') + '\n'

    file_lines[1] = str('touch .netrc') + '\n'
    file_lines[2] = str('echo "machine ' + machine_address +
                        ' login  ' + machine_user +
                        ' password ' + machine_password +
                        '" >> .netrc') + '\n'
    file_lines[3] = str('chmod 0600 .netrc') + '\n'
    file_lines[4] = str('touch .urs_cookies') + '\n'

    file_lines[5] = str('wget -P ' + folder_name_download)
    file_lines[5] += str(' --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies')
    file_lines[5] += str(' --keep-session-cookies --no-check-certificate --auth-no-challenge=on')
    file_lines[5] += str(' -r --reject "index.html*" -np -e robots=off')
    file_lines[5] += str(' --no-parent -A "' + file_name_src + '"')
    file_lines[5] += str(' ' + url_address_src) + '\n'

    file_lines[6] = str('mv ' + os.path.join(folder_name_download, path_address_src, file_name_src) +
                        ' ' + folder_name_src)

    # Open, write and close executable file
    file_handle = open(os.path.join(folder_name_download, file_name_download), 'w')
    file_handle.writelines(file_lines.values())
    file_handle.close()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define database settings
def get_machine_credential(machine_name="urs.earthdata.nasa.gov"):
    try:
        info = netrc.netrc()
        username, account, password = info.authenticators(machine_name)
    except Exception as e:
        logging.error(' ===> File netrc error: {0}'.format(str(e)))
        raise RuntimeError('Credentials are not available on netrc file')

    return username, password
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define machine settings
def define_machine_settings(machine_info):

    logging.info(' ---> Define machine configuration ... ')

    if 'name' in list(machine_info.keys()):
        machine_name = machine_info['name']
    else:
        logging.error(' ===> Machine name is not defined')
        raise IOError('Parameter is not defined in the configuration file.')
    if 'proxy' in list(machine_info.keys()):
        machine_local_proxy = machine_info['proxy']
    else:
        logging.error(' ===> Machine proxy is not defined')
        raise IOError('Parameter is not defined in the configuration file.')
    if 'user' in list(machine_info.keys()):
        machine_user = machine_info['user']
    else:
        logging.error(' ===> Machine user is not defined')
        raise IOError('Parameter is not defined in the configuration file.')
    if 'password' in list(machine_info.keys()):
        machine_password = machine_info['password']
    else:
        logging.error(' ===> Machine password is not defined')
        raise IOError('Parameter is not defined in the configuration file.')

    if 'data_folder' in list(machine_info.keys()):
        machine_data_folder = machine_info['data_folder']
    else:
        logging.error(' ===> Machine datasets folder is not defined')
        raise IOError('Parameter is not defined in the configuration file.')

    if 'data_root' in list(machine_info.keys()):
        machine_data_root = machine_info['data_root']
    else:
        logging.error(' ===> Machine datasets root path is not defined')
        raise IOError('Parameter is not defined in the configuration file.')

    logging.info(' ---> Define machine configuration ... DONE')

    return machine_name, machine_user, machine_password, machine_data_root, machine_data_folder, machine_local_proxy
# -------------------------------------------------------------------------------------
