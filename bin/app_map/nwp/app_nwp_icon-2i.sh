#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DYNAMICDATA - NWP ICON 2I - REALTIME'
script_version="1.7.0"
script_date='2024/10/16'

virtualenv_folder='/hydro/library/fp_libs_python_hyde/'
virtualenv_name='hyde_runner_libraries'
script_folder='/hydro/library/fp_package_hyde_v2/'

# Execution example:
# python app_nwp_icon_2i_main.py -settings_file configuration.json -time "YYYY-MM-DD HH:00"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file='/hydro/library/fp_package_hyde_v2/app/app_map/nwp/icon/app_nwp_icon_2i_main.py'
settings_file='/hydro/fp_tools_preprocessing/nwp/icon-2i/hyde_dynamicdata_nwp_icon-2i_realtime.json'

# Get lock information
file_lock_start_raw='hyde_lock_nwp_icon-2i_realtime_%YYYY%MM%DD_START.txt'
file_lock_end_raw='hyde_lock_nwp_icon-2i_realtime_%YYYY%MM%DD_END.txt'

file_lock_reinit=false
folder_lock_raw='/hydro/lock/nwp/'

# iterate over n days
time_period_days=0 # fix on 0 to provide actual time only, if providing a time period always add 1

# Get data information
file_list_expected=(
"%YYYY%MM%DD-icon-2i.t00z.ALB" 
"%YYYY%MM%DD-icon-2i.t00z.PRECI1" 
"%YYYY%MM%DD-icon-2i.t00z.RH2m" 
"%YYYY%MM%DD-icon-2i.t00z.SWH" 
"%YYYY%MM%DD-icon-2i.t00z.T2m" 
"%YYYY%MM%DD-icon-2i.t00z.VENTO10m"
)

folder_data_raw='/hydro/data/data_dynamic/source/nwp/icon-2i/'

# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
# time_now='2024-10-08 08:35'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Activate virtualenv
export PATH=$virtualenv_folder/bin:$PATH
source activate $virtualenv_name

# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ===> EXECUTION ..."
echo " "

# Iterate over days
time_run=$(date -d "$time_now" +'%Y-%m-%d %H:00')
for time_period_step in $(seq 0 $time_period_days); do
	
	#-----------------------------------------------------------------------------------------
    # Parse time information
    time_step=$(date -d "$time_run ${time_period_step} days ago" +'%Y-%m-%d %H:00')

	# Run python script (using setting and time)
	echo " ===> COMMAND LINE: python $script_path_app -settings_file $script_path_settings -time "$time_step" "
	echo " "
	# Execution pid
	execution_pid=$$
	#-----------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------
	# Get time information
	year=${time_step:0:4}
	month=${time_step:5:2}
	day=${time_step:8:2}

	# Define path data
	folder_data_def=${folder_data_raw/"%YYYY"/$year}
	folder_data_def=${folder_data_def/"%MM"/$month}
	folder_data_def=${folder_data_def/"%DD"/$day}

	folder_lock_def=${folder_lock_raw/"%YYYY"/$year}
	folder_lock_def=${folder_lock_def/"%MM"/$month}
	folder_lock_def=${folder_lock_def/"%DD"/$day}

	file_lock_start_def=${file_lock_start_raw/"%YYYY"/$year}
	file_lock_start_def=${file_lock_start_def/"%MM"/$month}
	file_lock_start_def=${file_lock_start_def/"%DD"/$day}

	file_lock_end_def=${file_lock_end_raw/"%YYYY"/$year}
	file_lock_end_def=${file_lock_end_def/"%MM"/$month}
	file_lock_end_def=${file_lock_end_def/"%DD"/$day}

	# Create folder(s)
	if [ ! -d "$folder_data_def" ]; then
		mkdir -p $folder_data_def
	fi
	if [ ! -d "$folder_lock_def" ]; then
		mkdir -p $folder_lock_def
	fi
	# ----------------------------------------------------------------------------------------	

	#-----------------------------------------------------------------------------------------
	# Iteration(s) to search input file(s)
	echo " ===> SEARCH SOURCE DATASETS ... "
	for file_name_raw in "${file_list_expected[@]}"
	do  
		 
		file_name_def=${file_name_raw/"%YYYY"/$year}
		file_name_def=${file_name_def/"%MM"/$month}
		file_name_def=${file_name_def/"%DD"/$day}

		path_file_def=$folder_data_def/$file_name_def
	   	
		echo " ====> SEARCH FILE: $path_file_def ... "
		if [ -f $path_file_def ]; then
		   	echo " ====> SEARCH FILE: $path_file_def ... DONE"
		    file_check=true
		else
		    echo " ====> SEARCH FILE: $path_file_def ... FAILED! FILE NOT FOUND!"
			file_check=false
			break
		fi
	done
	echo " ===> SEARCH SOURCE DATASETS ... DONE"
	echo " "
	#-----------------------------------------------------------------------------------------

	#-----------------------------------------------------------------------------------------
	# Flag to check data expected
	if $file_check; then
		
		#-----------------------------------------------------------------------------------------
		# File lock definition
		path_file_lock_def_start=$folder_lock_def/$file_lock_start_def 
		path_file_lock_def_end=$folder_lock_def/$file_lock_end_def
		
		# Init lock conditions
		echo " ===> INITIALIZE LOCK FILES ... "
		if $file_lock_reinit; then
		    # Delete lock files
		    if [ -f "$path_file_lock_def_start" ]; then
		       rm "$path_file_lock_def_start"
		    fi
		    if [ -f "$path_file_lock_def_end" ]; then
		       rm "$path_file_lock_def_end"
		    fi
		    echo " ===> INITIALIZE LOCK FILES ... DONE!"
		else
		    echo " ===> INITIALIZE LOCK FILES ... SKIPPED!"
		fi
		echo " "
		#-----------------------------------------------------------------------------------------
		
		#-----------------------------------------------------------------------------------------
		# Run check
		if [ -f $path_file_lock_def_start ] && [ -f $path_file_lock_def_end ]; then
		    
		    #-----------------------------------------------------------------------------------------
		    # Process completed
		    echo " ===> EXECUTION ... SKIPPED! ALL DATA WERE PROCESSED DURING A PREVIOUS RUN"
		    echo " "
		    #-----------------------------------------------------------------------------------------
		
		elif [ -f $path_file_lock_def_start ] && [ ! -f $path_file_lock_def_end ]; then
		    
		    #-----------------------------------------------------------------------------------------
		    # Process running condition
		    echo " ===> EXECUTION ... SKIPPED! SCRIPT IS STILL RUNNING ... WAIT FOR PROCESS END"
		    echo " "
		    #-----------------------------------------------------------------------------------------
		    
		elif [ ! -f $path_file_lock_def_start ] && [ ! -f $path_file_lock_def_end ]; then
		    
		    
		    #-----------------------------------------------------------------------------------------
		    # info run process start
		    echo " ===> RUN PROCESS ... "
		    
		    # Lock File START
		    time_analysis_start=$(date +"%Y-%m-%d %H:%S")
		    echo " ================================ " >> $path_file_lock_def_start
		    echo " ==== EXECUTION START REPORT ==== " >> $path_file_lock_def_start
		    echo " "
		    echo " ==== PID:" $execution_pid >> $path_file_lock_def_start
		    echo " ==== Algorithm: $script_name" >> $path_file_lock_def_start
		    echo " ==== RunTime: $time_analysis_start" >> $path_file_lock_def_start
		    echo " ==== ExecutionTime: $time_now" >> $path_file_lock_def_start
		    echo " ==== Status: RUNNING" >> $path_file_lock_def_start
		    echo " "
		    echo " ================================ " >> $path_file_lock_def_start

		    # Run python script (using setting and time)
		    python $script_file -settings_file $settings_file -time "$time_step"
		    
		    # Lock File END
		    time_analysis_end=$(date +"%Y-%m-%d %H:%S")
		    echo " ============================== " >> $path_file_lock_def_end
		    echo " ==== EXECUTION END REPORT ==== " >> $path_file_lock_def_end
		    echo " "
		    echo " ==== PID:" $execution_pid >> $path_file_lock_def_start
		    echo " ==== Algorithm: $script_name" >> $path_file_lock_def_end
		    echo " ==== RunTime: $time_analysis_end" >> $path_file_lock_def_end
		    echo " ==== ExecutionTime: $time_now" >> $path_file_lock_def_end
		    echo " ==== Status: COMPLETED" >>  $path_file_lock_def_end
		    echo " "
		    echo " ============================== " >> $path_file_lock_def_end
		    
		    # info run process start
		    echo " ===> RUN PROCESS ... DONE "
		    echo " "
		    
		    # Info script end
		    echo " ===> EXECUTION ... DONE"
		    echo " "
		    #-----------------------------------------------------------------------------------------
		    
	   else
		    
		    #-----------------------------------------------------------------------------------------
		    # Exit unexpected mode
		    echo " ===> EXECUTION ... FAILED! SCRIPT ENDED FOR UNKNOWN LOCK FILES CONDITION!"
		    #-----------------------------------------------------------------------------------------
		    
		fi
		#-----------------------------------------------------------------------------------------
		    
	else
		
		#-----------------------------------------------------------------------------------------
		# Info script end
		echo " ===> EXECUTION ... FAILED! SCRIPT INTERRUPTED ONE OR MORE SOURCE FILE(S) ARE UNAVAILABLE!"
		#-----------------------------------------------------------------------------------------
		
	fi

done

echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... BYE, BYE"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	


