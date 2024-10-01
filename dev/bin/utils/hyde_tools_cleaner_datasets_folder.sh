#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE UTILS - CLEANER DATASETS FOLDER(S) - HISTORY'
script_version="1.5.1"
script_date='2023/03/01'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file='hyde_tools_cleaner_datasets_folder.sh'
# Set flag to create the folder again
flag_create_folder=true

# Get folder information
folder_list_expected=(
"/home/dte/volume_destination_core_OLD/med_d01/" 
"/home/dte/volume_destination_core_OLD/med_d02/"
"/home/dte/volume_destination_core_OLD/med_d03/"
"/home/dte/volume_destination_core_OLD/med_d04/"
"/home/dte/volume_destination_core_OLD/med_d05/"
"/home/dte/volume_destination_core_OLD/med_d06/"
"/home/dte/volume_destination_core_OLD/med_d07/"
"/home/dte/volume_destination_core_OLD/med_d08/"
"/home/dte/volume_destination_core_OLD/med_d09/"
"/home/dte/volume_destination_core_OLD/med_d10/"
"/home/dte/volume_destination_core_OLD/med_d11/"
"/home/dte/volume_destination_core_OLD/med_d12/"
"/home/dte/volume_destination_core_OLD/med_d13/"
"/home/dte/volume_destination_core_OLD/med_d14/"
"/home/dte/volume_destination_core_OLD/med_d15/"
"/home/dte/volume_destination_core_OLD/med_d16/"
"/home/dte/volume_destination_core_OLD/med_d17/"
"/home/dte/volume_destination_core_OLD/med_d18/"
"/home/dte/volume_destination_core_OLD/med_d19/"
"/home/dte/volume_destination_core_OLD/med_d20/"
"/home/dte/volume_destination_core_OLD/med_d21/"
"/home/dte/volume_destination_core_OLD/med_d22/"
"/home/dte/volume_destination_core_OLD/med_d23/"
"/home/dte/volume_destination_core_OLD/med_d24/"
"/home/dte/volume_destination_core_OLD/med_d25/"
"/home/dte/volume_destination_core_OLD/med_d26/"
"/home/dte/volume_destination_core_OLD/med_d27/"
"/home/dte/volume_destination_core_OLD/med_d28/"
)

# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
# time_now='2020-11-20 09:35'
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Get time information
year=${time_now:0:4}
month=${time_now:5:2}
day=${time_now:8:2}
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> COMMAND LINE: " bash $script_file -time $time_now
echo " ===> EXECUTION ..."

# Execution pid
execution_pid=$$

# Iteration(s) to search folder 
echo " ====> SEARCH FOLDER ... "
for folder_name_raw in "${folder_list_expected[@]}"; do  
     
    folder_name_def=${folder_name_raw/"%YYYY"/$year}
    folder_name_def=${folder_name_def/"%MM"/$month}
    folder_name_def=${folder_name_def/"%DD"/$day}

    echo " =====> REMOVE FOLDER: $folder_name_def ... "
    if [ -d $folder_name_def ]; then
       	if rm -vrf $folder_name_def; then
       	    echo " =====> REMOVE FOLDER: $folder_name_def ... DONE"
       	else
       	    echo " =====> REMOVE FOLDER: $folder_name_def ... FAILED. ERROR IN DELETING FOLDER"
       	fi
    else
        echo " =====> REMOVE FOLDER: $folder_name_def ... SKIPPED! FOLDER NOT FOUND!"
    fi
    
    echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... "
    if [ "$flag_create_folder" = true ] ; then
		if [ ! -d $folder_name_def ]; then
		    if mkdir -p $folder_name_def; then
		        echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... DONE"
		    else
		        echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... FAILED. ERROR IN CREATING FOLDER"
		    fi
		else
		    echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... SKIPPED. FOLDER ALREADY EXISTS"
		fi
	else
		echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... SKIPPED. FLAG TO CREATE FOLDER IS NOT ACTIVE"
	fi
    
done
echo " ====> SEARCH FOLDER ... DONE"

echo " ===> EXECUTION ... DONE"
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	


