#!/bin/sh

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE UTILS - MANAGER DATASETS - OBS - KALMAN FILTER AIR TEMPERATURE - REALTIME'
script_version="2.0.0"
script_date='2020/12/08'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file='hyde_tools_manager_datasets_kf.sh'

folder_datasets='/hydro/data/data_dynamic/source/obs/kalman_filter/'
file_ext_datasets='.txt'

# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
# time_now='2020-11-20 09:35'
#-----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> COMMAND LINE: " bash $script_file -time $time_now
echo " ===> EXECUTION ..."

# Execution pid
execution_pid=$$

# Iterate over filename(s)
path_datasets=$folder_datasets"*"$file_ext_datasets
for file_datasets in $path_datasets; do

    # ----------------------------------------------------------------------------------------
    # Info start
    echo " ====> GET FILE ${file_datasets} ... "
    
    file_time=`date +%Y-%m-%d -r "$file_datasets"`

    file_year=$(echo $file_time| cut -d'-' -f 1)
    file_month=$(echo $file_time| cut -d'-' -f 2)
    file_day=$(echo $file_time| cut -d'-' -f 3)

    file_path=`dirname $file_datasets`
    file_name=`basename $file_datasets`

    file_name_ext="${file_name##*.}" 
    file_name_base="${file_name%.*}"
    # ----------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------
    # Copy file
    echo " =====> COPY FILE ... "
    if [ -f $file_datasets ]; then
        
        file_name_src=$file_name
        file_name_destination=${file_year}${file_month}${file_day}'_'$file_name_base'.'$file_name_ext

        file_path_src=$file_path
        file_path_destination=$file_path/$file_year/$file_month/$file_day

        if [ ! -d "$file_path_destination" ]; then
            mkdir -p $file_path_destination
        fi

        if cp -v $file_path_src/$file_name_src $file_path_destination/$file_name_destination; then
            echo " =====> COPY FILE ... DONE"
        else
            echo " =====> COPY FILE ... FAILED. ERROR IN COPY COMMAND"
        fi
         
    else
        echo " =====> COPY FILE ... FAILED, FILE NOT FOUND"
    fi  
    # ----------------------------------------------------------------------------------------
    
    # ----------------------------------------------------------------------------------------
    # Info end
    echo " ====> GET FILE ${file_datasets} ... DONE"
    # ----------------------------------------------------------------------------------------
        
done
    
echo " ===> EXECUTION ... DONE"
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	


