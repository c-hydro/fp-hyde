#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE UTILS - SYNC CHANGED FILE(S)'
script_version="1.0.5"
script_date='2019/10/17'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Define host
server_host='root@130.251.104.19'
# List product(s)
declare -a list_products=(
	"soil_moisture :: ascat-obs"
	"soil_moisture :: ascat-mod"
    "precipitation :: h03b" 
    "precipitation :: h05b" 
    "snow :: h10"
    "snow :: h12"
    "snow :: h13"
)

# Days period
declare -a list_days=(7 7 1 3 3 3 3)

# Declare local folder(s) list
declare -a list_folders=(
	"/home/hsaf/hsaf_datasets/dynamic/outcome/sm/"
	"/home/hsaf/hsaf_datasets/dynamic/outcome/rzsm/"
    "/home/hsaf/hsaf_datasets/dynamic/outcome/h03b/" 
    "/home/hsaf/hsaf_datasets/dynamic/outcome/h05b/" 
    "/home/hsaf/hsaf_datasets/dynamic/outcome/h10/"
    "/home/hsaf/hsaf_datasets/dynamic/outcome/h12/"
    "/home/hsaf/hsaf_datasets/dynamic/outcome/h13/"
)

# Declare filename(s) list
declare -a list_filename=(  
	"/home/hsaf/hsaf_datasets/dynamic/ancillary/sync_file/hsaf_sm_list.txt" 
	"/home/hsaf/hsaf_datasets/dynamic/ancillary/sync_file/hsaf_rzsm_list.txt"  
    "/home/hsaf/hsaf_datasets/dynamic/ancillary/sync_file/hsaf_h03b_list.txt" 
    "/home/hsaf/hsaf_datasets/dynamic/ancillary/sync_file/hsaf_h05b_list.txt" 
    "/home/hsaf/hsaf_datasets/dynamic/ancillary/sync_file/hsaf_h10_list.txt" 
    "/home/hsaf/hsaf_datasets/dynamic/ancillary/sync_file/hsaf_h12_list.txt" 
    "/home/hsaf/hsaf_datasets/dynamic/ancillary/sync_file/hsaf_h13_list.txt" 
)
# Declare server folder
declare -a dst_base_dir=/share/archivio/experience/data/HSAF
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."

# Iterate over folder(s) 
for index in ${!list_folders[*]}; do 

    # ----------------------------------------------------------------------------------------
    # Info step starting
	echo " ===> Product: "${list_products[$index]} " ... "
    echo " ===> Analyze folder: "${list_folders[$index]} 
    
    # Get filename(s)
    files_to_sync=$(find  ${list_folders[$index]} -mtime -${list_days[$index]}  -type f)
    # ----------------------------------------------------------------------------------------
    
    # ----------------------------------------------------------------------------------------
    # Iterate over filename(s)   
    for source_file in ${files_to_sync}; do
        
        # ----------------------------------------------------------------------------------------
        # Get information
        base_file=$(basename ${source_file})
        name_file="${base_file%.*}"
		
        old_IFS="$IFS"
        IFS='_'
        read -a file_name_tokens <<< "${base_file}"
        IFS="$old_IFS"
		      
        dst_dir=${dst_base_dir}/${file_name_tokens[1]}/${file_name_tokens[2]:0:4}/${file_name_tokens[2]:4:2}/${file_name_tokens[2]:6:2}/${file_name_tokens[2]:8:2}00
        dst_file=${dst_dir}/${base_file}
        # ----------------------------------------------------------------------------------------
        
        # ----------------------------------------------------------------------------------------
        # Transfer file from local to server
        echo " ====> Send ${source_file} to ${dst_file_zip} ... "
        
        # Check unzipped file availability on server
        if ! ssh $server_host test -e $dst_file; then
            
            # ----------------------------------------------------------------------------------------
			# Sync file from local to remote
            if ! ssh ${server_host} test -d ${dst_dir}; then
                ssh ${server_host} mkdir -p ${dst_dir}
            fi
            
            rsync -av -q --progress ${source_file} ${server_host}:${dst_file}
          
            if ! [ "$?" == "0" ]; then
                echo "ERROR in rsync. file: ${source_file}"
                #exit 3
            fi
            echo " ====> Send ${source_file} to ${dst_file} ... DONE"
            # ----------------------------------------------------------------------------------------
			
			# ----------------------------------------------------------------------------------------
			# Check compressed or uncompressed file
			dst_file_ext="${dst_file##*.}"
			if [[ "$dst_file_ext" == "gz" ]]; then

		        # ----------------------------------------------------------------------------------------
		        # Unzip file on server
		        echo " ====> Unzip ${dst_file} ... "
		        
		        ssh $server_host "test -e $dst_file"
		        if [ $? -eq 0 ]; then
		            
		            echo " =====> File exists on server"
		            ssh ${server_host} gzip -d ${dst_file}
		            #ssh ${server_host} rm ${dst_file_zip}
		            echo " ====> Unzip ${dst_file} ... DONE"

		        else
		            echo " =====> File does not exist on server"
		            echo " ====> Unzip ${dst_file} ... FAILED"
		        fi
			fi
			# ----------------------------------------------------------------------------------------
        
        else
			# ----------------------------------------------------------------------------------------
			# File already uploaded 
            echo " ====> Send ${source_file} to ${dst_file} ... SKIPPED. File previously sent."
			# ----------------------------------------------------------------------------------------
        fi
        # ----------------------------------------------------------------------------------------
        
    done    
    # ----------------------------------------------------------------------------------------
    
    # ----------------------------------------------------------------------------------------
    # Info step ending
    echo " ===> Product: "${list_products[$index]} " ... DONE"
    # ----------------------------------------------------------------------------------------

done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------
