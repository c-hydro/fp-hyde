#!/bin/bash -e

# ----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DOWNLOADER - HSAF PRODUCT SNOW H12'
script_version="1.5.0"
script_date='2018/07/25'

# Script argument(s)
data_folder_raw="/home/hsaf/hsaf_datasets/dynamic/source/h12/%YYYY/%MM/%DD/"
days=10
proxy=""

ftp_url=""
ftp_usr=""
ftp_pwd=""
ftp_folder=""
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Get time
time_now=$(date '+%Y-%m-%d %H:%M')
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
# ----------------------------------------------------------------------------------------

# Iterate over days
for day in $(seq 0 $days); do
    
    # ----------------------------------------------------------------------------------------
    # Get time step
	date_step=`date --date="${day} days ago" +%Y%m%d`
	# ----------------------------------------------------------------------------------------
	
    # ----------------------------------------------------------------------------------------
    # Info time start
    echo " =====> TIME_STEP: "$date_step" ===> START "

    # Define time step information
    date_get=$(date -u -d "$date_step" +"%Y%m%d%H")
    doy_get=$(date -u -d "$date_step" +"%j")

    year_get=$(date -u -d "$date_step" +"%Y")
    month_get=$(date -u -d "$date_step" +"%m")
    day_get=$(date -u -d "$date_step" +"%d")
    hour_get=$(date -u -d "$date_step" +"%H")
    # ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Define dynamic folder(s)
    data_folder_get=${data_folder_raw/'%YYYY'/$year_get}
    data_folder_get=${data_folder_get/'%MM'/$month_get}
    data_folder_get=${data_folder_get/'%DD'/$day_get}
    data_folder_get=${data_folder_get/'%HH'/$hour_get}
	# ----------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------	
	# Create folder(s)
	if [ ! -d "$data_folder_get" ]; then
		mkdir -p $data_folder_get
	fi
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Get file list from ftp
	ftp_file_list=`lftp << ftprem
	                set ftp:proxy ${proxy}
					open -u ${ftp_usr},${ftp_pwd} ${ftp_url}
					cd ${ftp_folder}
					cls -1 | sort -r | grep ${date_step} | sed -e "s/@//"
					close
					quit
ftprem`
    # ----------------------------------------------------------------------------------------
    

	# ----------------------------------------------------------------------------------------
	# Download file(s)	
	for ftp_file in ${ftp_file_list}; do
        
        echo -n " =====> DOWNLOAD FILE: ${ftp_file} IN ${data_folder_get}" 
        
		if ! [ -e ${data_folder_get}/${ftp_file} ]; then
			
			`lftp << ftprem
			            set ftp:proxy  ${proxy}
						open -u ${ftp_usr},${ftp_pwd} ${ftp_url}
						cd ${ftp_folder}
						get1 -o ${data_folder_get}/${ftp_file} ${ftp_file}
						close
						quit
ftprem`

			if [ $? -eq 0 ]; then
		 		echo " ==> DONE!"
			else
				echo " ==> FAILED [FTP ERROR] "
			fi
		
		else
			echo " $? ... SKIPPED! File previously downloaded!"
		fi
        # ----------------------------------------------------------------------------------------
        
	done
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Info time end
	echo " =====> TIME_STEP: "$date_step" ===> END "
    # ----------------------------------------------------------------------------------------

done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

