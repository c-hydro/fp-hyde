===========
Executables
===========

In this section, **executables** for different data type are presented; each of them run procedures to prepare data using a **python3** or **bash** scripts. These scripts are the link between the user machine and the applications developt for HyDE package. For example, they are used **to import** environmental variables (such as **PATH** and **LD_LIBRARY_PATH**) needed to execute applications or **to set up** jobs using **cron** scheduler. 
All applications are stored in the bin folder in the root of the package; an example of bin tree is reported:

::

    hyde-master
    ├── apps
    ├── **bin**
    │   ├── downloader
    │   │   ├── ground_network
    │   │   │   ├── rs
    │   │   │   └── ws
    │   │   ├── nwp
    │   │   │   ├── lami
    │   │   │   └── wrf
    │   │   └── satellite
    │   │       ├── modis
    │   │       └── hsaf
    │   ├── runner
    │   │   ├── ground_network
    │   │   │   ├── rs
    │   │   │   └── ws
    │   │   └── nwp
    │   │       ├── lami
    │   │       └── wrf
    │   ├── utils
    │   └── ...
    ├── docs
    ├── src
    │   ├── common
    │   └── hyde
    ├── test
    ├── AUTHORS.rst
    ├── CHANGELOG.rst
    ├── LICENSE.rst
    └── README.rst

As shows in the previous part, scripts are divided in downloaders, runners and generic utils. The **Downloaders** are used to get data from ftp, databases and other external sources. The **Runners** are used to execute applications to process data used by FloodPROOFS modelling system. The **Utils** are dedicated to solve a generic task to adapt data and procedures in special case to guarantee, for example, an operational use.

Downloader
**********

As previously said, the **first step** of procedures is about the downloading/collecting data from a database or a data repository; to perform this step, the **downloaders** used in HyDE package are usually written in **Python3** or **Bash** programming languages. In Hyde package at the moment are available scripts to download/collect:
 * ground network data;
 * numerical weather prediction data;
 * satellite data.

Python procedure
----------------

The procedures developt using **Python3** are organized in two part: 
    * a **main file** in Python3 format;
    * a **configuration file** in **JSON** format.

For example, the extraction of weather stations data is performed by an application available in HyDE in “/hyde-master/bin/downloader/ground_network/” named “hyde_downloader_{database_name}_ws.py”; for configuring this procedure, a JSON file usually named “hyde_downloader_{database}_ws.json” has to be filled in all of its part. The name of used database has to be specified by the users according with their settings. At the end, a output CSV file will be created with all data for each variable and for every timestep. 

Commonly, the script is organized as follows:

.. code-block:: python
    
    #!/usr/bin/python3 # declaration of interpreter

    """
    Procedure description
    """
    
    # Libraries
    import logging
    import numpy
    import os
    import time
    from argparse import ArgumentParser
    from json import load

    # Script main
    def main():

        # Info
        logging.info(' script start ... ')

        # Get algorithm arguments
        with open(get_args(), "r") as file_obj:
            file_data = load(file_obj)

        ... 
        
        # Call func_01
        result_1 = func_01(arguments_1)
        
        ...

        # Call func_02
        result_2 = func_02(result_1, arguments_2)

        if res2 is None:
            logging.warning(' res2 is None!')
        ...

        try:
            result_03 = func_03()
        except:
            logging.error('func_03 not implemented')
            raise NotImplementedError('check your code to add func_03')

        ...

        # Info 
        logging.info(' ... script end')

    # Method to set logging information
    def set_log(logger_file='log.txt',
                logger_msg='%(asctime)s %(name)-12s %(levelname)-8s %(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'):
    
        # Remove old logging file
        if exists(logger_file):
            remove(logger_file)
    
        # Open logging basic configuration
        logging.basicConfig(level=logging.INFO,
                            format=logger_msg,
                            filename=logger_file,
                            filemode='w')
    
        # Set logger handle
        log_handle_1 = logging.FileHandler(logger_file, 'w')
        log_handle_2 = logging.StreamHandler()
        # Set logger level
        log_handle_1.setLevel(logging.DEBUG)
        log_handle_2.setLevel(logging.DEBUG)
        # Set logger formatter
        log_formatter = logging.Formatter(logger_msg)
        log_handle_1.setFormatter(log_formatter)
        log_handle_2.setFormatter(log_formatter)
        # Add handle to logging
        logging.getLogger('').addHandler(log_handle_1)
        logging.getLogger('').addHandler(log_handle_2)


    # Method to get script argument(s)
    def get_args(settings_file_default='configuration.json'):
        parser_obj = ArgumentParser()
        parser_obj.add_argument('-settings_file', action="store", dest="settings_file")
        parser_values = parser_obj.parse_args()
    
        if oParserValue.settings_file:
            filename = parser_values.settings_file
        else:
            filename = settings_file_default
    
        return filename

    def func_01(args):
        ...
        return res1
  
    def func_02(data, args):
        ...
        return res2

    # Call script from external library
    if __name__ == "__main__":
        main()

Bash procedure
--------------

The procedures developt using **Bash** consist in a **script** with settings specified in the first part of the code. An example of Bash script is reported below:

.. code-block:: bash

    #!/bin/bash -e # declaration of interpreter
    
    # Script information
    script_name='HYDE DOWNLOADER - HSAF PRODUCT PRECIPITATION H03B'
    script_version="2.0.2"
    script_date='2019/10/07'
    
    # Script argument(s)
    data_folder_raw="/source/h03b/%YYYY/%MM/%DD/"
    days=5
    proxy="http://xxx.xxx.xxx.xxx:xxxx"
    
    ftp_url="ftp.meteo.it"
    ftp_usr="********" 
    ftp_pwd="********" 
    ftp_folder="/products/h03B/h03B_cur_mon_data/"
    
    str_grib='fdk'
    str_tmp_step1='fdk'
    str_tmp_step2='fulldisk'
    str_nc='europe'
    
    list_var_drop='x,y'
    var_rename_1='IRRATE_no_level,IRRATE_Data'
    var_rename_2='IRRATE_surface,IRRATE_QualityIndex'
    
    domain_bb='-15,30,30,60'
    
    wgrib2_exec="/bin/wgrib2"
    ncks_exec="//bin/ncks"
    ncrename_exec="/bin/ncrename"
    cdo_exec="/bin/cdo"

    ...

In general, the downloaders written in Bash are available in HyDE in “/hyde-master/bin/downloader/{application_type}/” named “hyde_downloader_{application_type}_{product_type}.sh”. Usually, some external applications, such as lftp_, rsync_, wgrib2_, cdo_, nco_ are used to execute operations over variables to change resolutions. domain reference, projections and so on.

.. _lftp: https://lftp.yar.ru/
.. _rsync: https://linux.die.net/man/1/rsync
.. _wgrib2: https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/
.. _cdo: https://code.mpimet.mpg.de/projects/cdo
.. _nco: http://nco.sourceforge.net/

Runner
******

Once the static and dynamic datasets are collected, in HyDE package some scripts written in **Bash** programming are available to run applications (usually named **runners**). In HyDE package, they are available in “/hyde-master/bin/runner/" and are divided following as follows:
 * ground network executables;
 * numerical weather prediction executables;
 * satellite executables.

The procedures developt using Bash consist in a **script** with settings specified in the first part of the code. An example of a script is reported below:

.. code-block:: bash

    #!/bin/bash -e
    
    #-----------------------------------------------------------------------------------------
    # Script information
    script_name='HYDE RUNNER - HSAF ASCAT OBS [METOP-SM] REALTIME - NRT'
    script_version="1.0.0"
    script_date='2019/08/29'
    
    script_folder='/home/hyde-master/'
    
    virtual_env_folder='/home/libs_python3/bin/'
    virtual_env_name='libs_env_python3'
    #-----------------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------------
    # Get file information
    script_file='/home/hyde-master/apps/hsaf/soil_moisture/HYDE_DynamicData_HSAF_ASCAT_OBS_NRT.py'
    setting_file='/home/hyde-master/apps/hsaf/soil_moisture/hyde_configuration_hsaf_ascat_obs_nrt_realtime.json'
    
    # Get information (-u to get gmt time)
    time_now=$(date -u +"%Y%m%d%H00")
    #-----------------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------------
    # Add path to pythonpath
    export PYTHONPATH="${PYTHONPATH}:$script_folder"
    # Add virtual env
    export PATH=$virtual_env_folder:$PATH
    source activate $virtual_env_name
    #-----------------------------------------------------------------------------------------
    
    # ----------------------------------------------------------------------------------------
    # Info script start
    echo " ==================================================================================="
    echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
    echo " ==> START ..."
    echo " ==> COMMAND LINE: " python $script_file -settingfile $setting_file -time $time_now
    
    # Run python script (using setting and time)
    python3 $script_file -settingsfile $setting_file -time $time_now
    
    # Info script end
    echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
    echo " ==> ... END"
    echo " ==> Bye, Bye"
    echo " ==================================================================================="
    # ----------------------------------------------------------------------------------------

Usually, as we can see in the previous snippet, the **runners** are **configured** using a **python virtual environment** created by the miniconda_ system. It is possible to install all libraries and applications using the `virtual environments of FloodProofs`_ modelling system  The configuration of miniconda virtual environment is performed in the runners by the following code lines:

.. code-block:: bash

    ...
    
    # Add path to pythonpath
    export PYTHONPATH="${PYTHONPATH}:$script_folder"
    # Add virtual env
    export PATH=$virtual_env_folder:$PATH
    source activate $virtual_env_name

    ...

.. _virtual environments of FloodProofs: https://github.com/c-hydro/fp-env
.. _miniconda: https://conda.io/miniconda.html


Utils
*****

The **utilities** executables are ancillary scripts that are used to:
    * **change** the default results of an HyDE applications;
    * **manage** the content of the modelling system folders (deleting, syncroning and so on);
    * **monitor** the machine memory (RAM, process, swap and so on);
    * **synchronize** the data between different machines;
    * ...

In HyDE package, they are available in “/hyde-master/bin/utils/". Usually, they are used to solve a **specific problem** or request in developing FloodProofs modelling system.

Scheduler and Environment configuration
***************************************

Scheduler configuration - Crontab
---------------------------------

The first step to configure the executables file (downloaders and runners) is to use the Crontab_ **(CRON TABle)** scheduler to automatically launch HyDE executables. The Crontab is a file which contains the schedule of cron entries to be run and at specified times. File location varies by operating systems. Moreover, cron job or cron schedule is a specific set of execution instructions specifying day, time and command to execute. Crontab can have multiple execution statements.

.. code-block:: bash

    # HYDE - DATAPROCESSING - GroundNetwork - WeatherStations
    25 * * * * . $HOME/.profile; $HOME/hyde-master/bin/runner/ground_network/hyde_runner_groundnetwork_ws.sh
    # HYDE - DATAPROCESING - NWP  WRF
    30 7,8,19,20 * * * . $HOME/.profile; $HOME/hyde-master/bin/runner/wrf/hyde_runner_nwp_wrf.sh
    # HYDE - DATAPROCESING - RFARM WRF
    35 7,8,19,20 * * * . $HOME/.profile; $HOME/hyde-master/bin/runner/rfarm/hyde_runner_rfarm_wrf.sh
    # HYDE - UTILS - CLEANER - HOURLY/DAILY
    0 0-23 * * * . $HOME/.profile; $HOME/hyde-master/bin/utils/hyde_utils_cleaner_folders.sh

For editing or updating Crontab file, the users have to use the following command in the terminal:

.. code-block:: bash

    >> crontab -e

.. _Crontab: https://linux.die.net/man/5/crontab


Environment configuration - profile
------------------------------------

The second step, to configure the HyDE executables for performing data processing or models running, is
to set the profile_ file in the machine environment. The **.profile** file in Linux comes under the System startup files. File like /etc/profile controls variables for profile of all users of the system whereas, .profile allows you to customize your own environment. The .profile file is present in the user home ($HOME) directory and lets you customize user's individual working environment.
The .profile file contains user's individual profile that overrides the variables set in the /etc/profile file. 

An example of .profile file is reported below:

.. code-block:: bash

    # Export library for flood proofs modelling system
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$HOME/library/zlib-1.2.11/lib/
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$HOME/library/hdf5-1.8.17/lib/
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$HOME/library/netcdf-4.1.2/lib/
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$HOME/library/geos-3.5.0/lib/
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$HOME/library/proj-4.9.2/lib/
    
    # Export binaries for flood proofs modelling system
    export PATH=$HOME/library/hdf5-1.8.17/bin:$PATH
    export PATH=$HOME/library/zlib-1.2.11/bin:$PATH
    export PATH=$HOME/library/netcdf-4.1.2/bin:$PATH
    export PATH=$HOME/library/geos-3.5.0/bin:$PATH
    export PATH=$HOME/library/proj-4.9.2/bin:$PATH

In this example, the user filled .profile with export commands for LD_LIBRARY_PATH and PATH environment variables. After this step, the executbales are ready to run using a particular or a different version of a library. Sometimes, libraries set by default in a linux machine are not enough to solve a specific problem. 


.. _profile: http://www.theunixschool.com/2011/07/what-is-profile-file.html?m=1






