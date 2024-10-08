#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DYNAMICDATA - NWP LAMI 2I - EXAMPLE'
script_version="1.6.0"
script_date='2020/11/30'

virtualenv_folder='/hydro/library/fp_libs_python3/'
virtualenv_name='virtualenv_python3'
script_folder='/hydro/library/hyde/'

# Execution example:
# python3 app_nwp_lami_2i.py -settings_file hyde_dynamicdata_nwp_lami-2i.json -time "2020-11-02 12:00"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file='app_nwp_lami_2i.py'
settings_file='app_nwp_lami_2i_old.json'

# Get lock information
file_lock_start='hyde_lock_nwp_lami-2i_example_START.txt'
file_lock_end='hyde_lock_nwp_lami-2i_example_END.txt'

file_lock_init=true
folder_lock_raw='/lock/nwp/'

# Get data information
file_list_expected=(
"%YYYY%MM%DD-lami-2i.t00z.ALB" 
"%YYYY%MM%DD-lami-2i.t00z.PRECI1" 
"%YYYY%MM%DD-lami-2i.t00z.RH2m" 
"%YYYY%MM%DD-lami-2i.t00z.SWH" 
"%YYYY%MM%DD-lami-2i.t00z.T2m" 
"%YYYY%MM%DD-lami-2i.t00z.VENTO10m"
)

folder_data_raw='/hydro/data/data_dynamic/source/nwp/lami_old-2i/'

# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
# time_now='2020-11-20 09:35'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Activate virtualenv
export PATH=$virtualenv_folder/bin:$PATH
source activate $virtualenv_name

# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Get time information
year=${time_now:0:4}
month=${time_now:5:2}
day=${time_now:8:2}

# Define path data
folder_data_def=${folder_data_raw/"%YYYY"/$year}
folder_data_def=${folder_data_def/"%MM"/$month}
folder_data_def=${folder_data_def/"%DD"/$day}

folder_lock_def=${folder_lock_raw/"%YYYY"/$year}
folder_lock_def=${folder_lock_def/"%MM"/$month}
folder_lock_def=${folder_lock_def/"%DD"/$day}

# Create folder(s)
if [ ! -d "$folder_data_def" ]; then
	mkdir -p $folder_data_def
fi
if [ ! -d "$folder_lock_def" ]; then
	mkdir -p $folder_lock_def
fi
# ----------------------------------------------------------------------------------------	


# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> COMMAND LINE: " python3 $script_file -settings_file $settings_file -time $time_now
echo " ===> EXECUTION ..."

# Execution pid
execution_pid=$$
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Iteration(s) to search input file(s)
echo " ====> SEARCH SOURCE DATASETS ... "
for file_name_raw in "${file_list_expected[@]}"
do  
     
    file_name_def=${file_name_raw/"%YYYY"/$year}
    file_name_def=${file_name_def/"%MM"/$month}
    file_name_def=${file_name_def/"%DD"/$day}

    path_file_def=$folder_data_def/$file_name_def
   	
	echo " =====> SEARCH FILE: $path_file_def ... "
    if [ -f $path_file_def ]; then
       	echo " =====> SEARCH FILE: $path_file_def ... DONE"
        file_check=true
    else
        echo " =====> SEARCH FILE: $path_file_def ... FAILED! FILE NOT FOUND!"
		file_check=false
		break
    fi
done
echo " ====> SEARCH SOURCE DATASETS ... DONE"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Flag to check data expected
if $file_check; then
    
    #-----------------------------------------------------------------------------------------
    # File lock definition
    path_file_lock_def_start=$folder_lock_def/$file_lock_start  
    path_file_lock_def_end=$folder_lock_def/$file_lock_end
    
    # Init lock conditions
    echo " ====> INITILIZE LOCK FILES ... "
    if $file_lock_init; then
        # Delete lock files
        if [ -f "$path_file_lock_def_start" ]; then
           rm "$path_file_lock_def_start"
        fi
        if [ -f "$path_file_lock_def_end" ]; then
           rm "$path_file_lock_def_end"
        fi
        echo " ====> INITILIZE LOCK FILES ... DONE!"
    else
        echo " ====> INITILIZE LOCK FILES ... SKIPPED!"
    fi
    #-----------------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------------
    # Run check
    if [ -f $path_file_lock_def_start ] && [ -f $path_file_lock_def_end ]; then
        
        #-----------------------------------------------------------------------------------------
        # Process completed
        echo " ===> EXECUTION ... SKIPPED! ALL DATA WERE PROCESSED DURING A PREVIOUSLY RUN"
        #-----------------------------------------------------------------------------------------
    
    elif [ -f $path_file_lock_def_start ] && [ ! -f $path_file_lock_def_end ]; then
        
        #-----------------------------------------------------------------------------------------
        # Process running condition
        echo " ===> EXECUTION ... SKIPPED! SCRIPT IS STILL RUNNING ... WAIT FOR PROCESS END"
        #-----------------------------------------------------------------------------------------
        
    elif [ ! -f $path_file_lock_def_start ] && [ ! -f $path_file_lock_def_end ]; then
        
        
        #-----------------------------------------------------------------------------------------
        # Lock File START
        time_step=$(date +"%Y-%m-%d %H:%S")
        echo " ================================ " >> $path_file_lock_def_start
        echo " ==== EXECUTION START REPORT ==== " >> $path_file_lock_def_start
        echo " "
        echo " ==== PID:" $execution_pid >> $path_file_lock_def_start
        echo " ==== Algorithm: $script_name" >> $path_file_lock_def_start
        echo " ==== RunTime: $time_step" >> $path_file_lock_def_start
        echo " ==== ExecutionTime: $time_now" >> $path_file_lock_def_start
        echo " ==== Status: RUNNING" >> $path_file_lock_def_start
        echo " "
        echo " ================================ " >> $path_file_lock_def_start

        # Run python script (using setting and time)
        python3 $script_file -settings_file $settings_file -time "$time_now"
        
        # Lock File END
        time_step=$(date +"%Y-%m-%d %H:%S")
        echo " ============================== " >> $path_file_lock_def_end
        echo " ==== EXECUTION END REPORT ==== " >> $path_file_lock_def_end
        echo " "
        echo " ==== SCRIPT END" >> $path_file_lock_def_end
        echo " ==== PID:" $execution_pid >> $path_file_lock_def_start
        echo " ==== Algorithm: $script_name" >> $path_file_lock_def_end
        echo " ==== RunTime: $time_step" >> $path_file_lock_def_end
        echo " ==== ExecutionTime: $time_now" >> $path_file_lock_def_end
        echo " ==== Status: COMPLETED" >>  $path_file_lock_def_end
        echo " "
        echo " ============================== " >> $path_file_lock_def_end
        
        # Info script end
        echo " ===> EXECUTION ... DONE"
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

echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	


