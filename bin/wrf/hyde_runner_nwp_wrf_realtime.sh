#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE RUNNER - NWP WRF - REALTIME'
script_version="1.5.1"
script_date='2019/10/18'

script_folder='/share/c-hydro/hyde-master/'

virtual_env_folder='/share/c-hydro/library/virtualenv_python3/bin/'
virtual_env_name='virtualenv_python3'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/share/c-hydro/hyde-master/apps/wrf/HYDE_DynamicData_NWP_WRF.py'
settings_file='/share/c-hydro/hyde-master/apps/wrf/hyde_configuration_nwp_wrf_barbados_realtime.json'

env_flag=true

file_lock_start_raw='nwp_dynamicdata_wrf_lock_%YYYY%MM%DD%HH00_realtime_START.txt'
file_lock_end_raw='nwp_dynamicdata_wrf_lock_%YYYY%MM%DD%HH00_realtime_END.txt'

file_list=("wrfout_d02_%YYYY-%MM-%DD_%HH:00:00_PLEV_BIL.nc" )

folder_data_raw='/share/c-hydro/data/dynamic/source/wrf/%YYYY/%MM/%DD/%HH00/'
folder_lock_raw='/share/c-hydro/lock/'

time_n_min=0
time_n_max=36

# Get information (-u to get gmt time)
time_system=$(date +"%Y-%m-%d %H:00")
# time_system=$(date -u +"%Y-%m-%d %H:00")
# time_system='2019-10-17 15:32' # DEBUG 
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
# Add virtual env
export PATH=$virtual_env_folder:$PATH
source activate $virtual_env_name
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Set hour of the model starting from time system
hour_system=$(date +%H -d "$time_system")
if [[ "$hour_system" -ge 12 ]]; then
	time_run=$(date +%Y%m%d1200 -d "$time_system")
	time_now="$(date +%Y-%m-%d -d "$time_system") 12:00"
	time_now=$(date -d "$time_now" +'%Y-%m-%d %H:%M' )
else
	time_run=$(date +%Y%m%d0000 -d "$time_system")
	time_now="$(date +%Y-%m-%d -d "$time_system") 00:00"
	time_now=$(date -d "$time_now" +'%Y-%m-%d %H:%M' )
fi
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
echo " ==> COMMAND LINE: " python3 $script_file -settings_file $settings_file -time $time_now [time_system $time_system]

# ----------------------------------------------------------------------------------------	
# Get time information
time_exe=$(date)

year=${time_now:0:4}
month=${time_now:5:2}
day=${time_now:8:2}
hour=${time_now:11:2}

# Define path data
folder_data_def=${folder_data_raw/"%YYYY"/$year}
folder_data_def=${folder_data_def/"%MM"/$month}
folder_data_def=${folder_data_def/"%DD"/$day}
folder_data_def=${folder_data_def/"%HH"/$hour}

folder_lock_def=${folder_lock_raw/"%YYYY"/$year}
folder_lock_def=${folder_lock_def/"%MM"/$month}
folder_lock_def=${folder_lock_def/"%DD"/$day}
folder_lock_def=${folder_lock_def/"%HH"/$hour}

# Define locking file(s)
file_lock_start_def=${file_lock_start_raw/"%YYYY"/$year}
file_lock_start_def=${file_lock_start_def/"%MM"/$month}
file_lock_start_def=${file_lock_start_def/"%DD"/$day}
file_lock_start_def=${file_lock_start_def/"%HH"/$hour}

file_lock_end_def=${file_lock_end_raw/"%YYYY"/$year}
file_lock_end_def=${file_lock_end_def/"%MM"/$month}
file_lock_end_def=${file_lock_end_def/"%DD"/$day}
file_lock_end_def=${file_lock_end_def/"%HH"/$hour}
# ----------------------------------------------------------------------------------------	

# ----------------------------------------------------------------------------------------
# Check environment flag
if $env_flag; then

	# ----------------------------------------------------------------------------------------
	# Iteration(s) to search input file(s)
	for file_name_raw in "${file_list[@]}"
	do  
		
		for ((i=$time_n_min; i<=$time_n_max; i++)); do      
			
			time_step=$(date -d "$time_now $i hours" '+%Y-%m-%d %H:%M')   

			year_step=${time_step:0:4}
			month_step=${time_step:5:2}
			day_step=${time_step:8:2}
			hour_step=${time_step:11:2}

			file_name_def=${file_name_raw/"%YYYY"/$year_step}
			file_name_def=${file_name_def/"%MM"/$month_step}
			file_name_def=${file_name_def/"%DD"/$day_step}
			file_name_def=${file_name_def/"%HH"/$hour_step}

			path_file_def=$folder_data_def/$file_name_def
		   	
			echo " ===> SEARCH FILE: $path_file_def ... "
			if [ -f $path_file_def ]; then
			   	echo " ===> SEARCH FILE: $path_file_def ... DONE"
				file_check=true
			else
				echo " ===> SEARCH FILE: $path_file_def ... FAILED! FILE NOT FOUND!"
				file_check=false
				break
			fi

		done

	done

	if $file_check; then
		echo " ===> SEARCH FILE(S) COMPLETED. ALL FILES ARE AVAILABLE"
	else
		echo " ===> SEARCH FILE(S) INTERRUPTED. ONE OR MORE FILE(S) IN SEARCHING PERIOD ARE NOT AVAILABLE"
	fi

else
	# ----------------------------------------------------------------------------------------
	# Condition for environment flag deactivated
	echo " ===> SEARCH FILE(S) SKIPPED. ENVIRONMENT FLAG IS DEACTIVATED"
	file_check=true
	# ----------------------------------------------------------------------------------------
fi
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Run according with file(s) availability
if $file_check; then
	
	# ----------------------------------------------------------------------------------------	
	# Create folder(s)
	if [ ! -d "$folder_data_def" ]; then
		mkdir -p $folder_data_def
	fi
	if [ ! -d "$folder_lock_def" ]; then
		mkdir -p $folder_lock_def
	fi
	# ----------------------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------------
    # Start
    echo " ===> EXECUTE SCRIPT ... "
    path_file_lock_def_start=$folder_lock_def/$file_lock_start_def  
    path_file_lock_def_end=$folder_lock_def/$file_lock_end_def

	if ! $env_flag; then
		if [ -f $path_file_lock_def_start ]; then
			rm $path_file_lock_def_start
		fi
		if [ -f $path_file_lock_def_end ]; then
			rm $path_file_lock_def_end
		fi
	fi
    #-----------------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------------
    # Run check
    if [ -f $path_file_lock_def_start ] && [ -f $path_file_lock_def_end ]; then
        
        #-----------------------------------------------------------------------------------------
        # Process completed
        echo " ===> EXECUTE SCRIPT ... SKIPPED!"
		echo " ===> ALL DATA HAVE BEEN PROCESSED DURING A PREVIOUSLY RUN"
        #-----------------------------------------------------------------------------------------
    
    elif [ -f $path_file_lock_def_start ] && [ ! -f $path_file_lock_def_end ]; then
        
        #-----------------------------------------------------------------------------------------
        # Process running condition
        echo " ===> EXECUTE SCRIPT ... SKIPPED!"
		echo " ===> SCRIPT STILL RUNNING ... WAIT FOR PROCESS END"
        #-----------------------------------------------------------------------------------------
        
    elif [ ! -f $path_file_lock_def_start ] && [ ! -f $path_file_lock_def_end ]; then
        
        #-----------------------------------------------------------------------------------------
        # Lock File START
        time_step=$(date +"%Y%m%d%H%S")
        echo " ==== SCRIPT START" >> $path_file_lock_def_start
        echo " ==== Script name: $script_name" >> $path_file_lock_def_start
        echo " ==== Script run time: $time_step" >> $path_file_lock_def_start
        echo " ==== Script exe time: $time_exe" >> $path_file_lock_def_start
        echo " ==== Script execution running ..." >> $path_file_lock_def_start
        #-----------------------------------------------------------------------------------------
		
		#-----------------------------------------------------------------------------------------
		# Run python script (using setting and time)
		python3 $script_file -settings_file $settings_file -time $time_run
		#-----------------------------------------------------------------------------------------
        
        #-----------------------------------------------------------------------------------------
        # Lock File END
        time_step=$(date +"%Y%m%d%H%S")
        echo " ==== SCRIPT END" >> $path_file_lock_def_end
        echo " ==== Script name: $script_name" >> $path_file_lock_def_end
        echo " ==== Script run time: $time_step" >> $path_file_lock_def_end
        echo " ==== Script exe time: $time_exe" >> $path_file_lock_def_end
        echo " ==== Script execution finished" >>  $path_file_lock_def_end
        #-----------------------------------------------------------------------------------------
        
        #-----------------------------------------------------------------------------------------
        # Exit
        echo " ===> EXECUTE SCRIPT ... DONE!"
        #-----------------------------------------------------------------------------------------
        
    else
        
        #-----------------------------------------------------------------------------------------
        # Exit unexpected mode
        echo " ===> EXECUTE SCRIPT ... FAILED!"
		echo " ===> SCRIPT ENDED FOR UNKNOWN LOCK CONDITION!"
        #-----------------------------------------------------------------------------------------
        
    fi
    #-----------------------------------------------------------------------------------------

else

    #-----------------------------------------------------------------------------------------
    # Exit
    echo " ===> EXECUTE SCRIPT ... FAILED!"
	echo " ===> SCRIPT INTERRUPTED! ONE OR MORE INPUT FILE(S) ARE UNAVAILABLE!"
    #-----------------------------------------------------------------------------------------
    
fi
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

