#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE RUNNER - NWP LAMI 2I - REALTIME'
script_version="1.5.0"
script_date='2019/09/13'

# LOCAL
script_folder='/home/dpc-marche/library/hyde-master/'

virtual_env_folder=$HOME'/fp_libs_python/bin/'
virtual_env_name='fp_env_python'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information

# LOCAL
script_file='/home/dpc-marche/library/hyde-master/apps/lami_old/HYDE_DynamicData_NWP_LAMI_2i.py'
setting_file='/home/dpc-marche/library/hyde-master/apps/lami_old/hyde_configuration_nwp_lami_2i_realtime.json'

file_lock_start='nwp_dynamicdata_lami-2i_lock_local_START.txt'
file_lock_end='nwp_dynamicdata_lami-2i_lock_local_END.txt'

file_list=(
"%YYYY%MM%DD-lami-2i.t00z.ALB" 
"%YYYY%MM%DD-lami-2i.t00z.PRECI1" 
"%YYYY%MM%DD-lami-2i.t00z.RH2m" 
"%YYYY%MM%DD-lami-2i.t00z.SWH" 
"%YYYY%MM%DD-lami-2i.t00z.T2m" 
"%YYYY%MM%DD-lami-2i.t00z.VENTO10m"
)

folder_data_raw='/hydro/data/dynamic_data/source/nwp/lami_old-2i/'
folder_lock_raw='/home/dpc-marche/lock/'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y%m%d%H00")
time_exe=$(date)
# time_now='201909160923' # DEBUG
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
echo " ==> COMMAND LINE: " python3 $script_file -settingsfile $setting_file -time $time_now
# ----------------------------------------------------------------------------------------	

# ----------------------------------------------------------------------------------------	
# Get time information
year=${time_now:0:4}
month=${time_now:4:2}
day=${time_now:6:2}

# Define path data
folder_data_def=${folder_data_raw/"%YYYY"/$year}
folder_data_def=${folder_data_def/"%MM"/$month}
folder_data_def=${folder_data_def/"%DD"/$day}

folder_lock_def=${folder_lock_raw/"%YYYY"/$year}
folder_lock_def=${folder_lock_def/"%MM"/$month}
folder_lock_def=${folder_lock_def/"%DD"/$day}
# ----------------------------------------------------------------------------------------	

# ----------------------------------------------------------------------------------------	
# Create folder(s)
if [ ! -d "$folder_data_def" ]; then
	mkdir -p $folder_data_def
fi
if [ ! -d "$folder_lock_def" ]; then
	mkdir -p $folder_lock_def
fi
# ----------------------------------------------------------------------------------------

# Iteration(s) to search input file(s)
for file_name_raw in "${file_list[@]}"
do  
     
    file_name_def=${file_name_raw/"%YYYY"/$year}
    file_name_def=${file_name_def/"%MM"/$month}
    file_name_def=${file_name_def/"%DD"/$day}

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

if $file_check; then
	
    #-----------------------------------------------------------------------------------------
    # Start
    echo " ===> EXECUTE SCRIPT ... "
    path_file_lock_def_start=$folder_lock_def/$file_lock_start  
    path_file_lock_def_end=$folder_lock_def/$file_lock_end
    #-----------------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------------
    # Run check
    if [ -f $path_file_lock_def_start ] && [ -f $path_file_lock_def_end ]; then
        
        #-----------------------------------------------------------------------------------------
        # Process completed
        echo " ===> EXECUTE SCRIPT ... SKIPPED!"
		echo " ===> ALL DATA WEWE PROCESSED DURING A PREVIOUSLY RUN"
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
		python3 $script_file -settingsfile $setting_file -time $time_now
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
	

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------


