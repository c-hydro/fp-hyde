#!/bin/bash -e

# ----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DOWNLOADER - HSAF PRODUCT PRECIPITATION H05B'
script_version="2.0.2"
script_date='2019/10/07'

# Script argument(s)
data_folder_raw="/home/hsaf/hsaf_datasets/dynamic/source/h05b/%YYYY/%MM/%DD/"
days=5
proxy=""

ftp_url=""
ftp_usr=""
ftp_pwd=""
ftp_folder="/products/h05B/h05B_cur_mon_data/"

str_grib='fdk'
str_tmp_step1='fdk'
str_tmp_step2='fulldisk'
str_nc='europe'

list_var_drop='x,y'
var_rename_1='ESTP_no_level,ESTP_Data'
var_rename_2='ESTP_surface,ESTP_QualityIndex'

domain_bb='-15,30,30,60'

wgrib2_exec="/home/hsaf/library/wgrib2_basic/wgrib2"
ncks_exec="/home/hsaf/library/nco-4.6.0/bin/ncks"
ncrename_exec="/home/hsaf/library/nco-4.6.0/bin/ncrename"
cdo_exec="/home/hsaf/library/cdo-1.7.2rc3_NC-4.1.2_HDF-1.8.17/bin/cdo"

# Export library path dependecies
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/hsaf/library/grib_api-1.15.0/lib/
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
    echo " ===> TIME_STEP: "$date_step" ===> START "

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
        
        echo -n " ====> DOWNLOAD FILE: ${ftp_file} IN ${data_folder_get} ..." 
        
		if ! [ -e ${data_folder_get}/${ftp_file} ]; then
			
			`lftp << ftprem
			            set ftp:proxy  ${proxy}
						open -u ${ftp_usr},${ftp_pwd} ${ftp_url}
						cd ${ftp_folder}
						get1 -o ${data_folder_get}/${ftp_file} ${ftp_file}
						close
						quit
ftprem`

			if [ $? -eq 0 ] > /dev/null 2>&1; then
		 		echo " DONE!"
			else
				echo " FAILED [FTP ERROR] "
			fi
		
		else
			echo " SKIPPED! File previously downloaded!"
		fi
        # ----------------------------------------------------------------------------------------
        
	done
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Iterate on file(s) for converting to netcdf over domain
	for file_name_zip in ${ftp_file_list}; do
        
        # ----------------------------------------------------------------------------------------
        # Filename(s) definition(s)
        file_name_tmp=$(basename -- "$file_name_zip")
        file_ext_tmp="${file_name_tmp##*.}"
        
        file_name_grib="${file_name_tmp%.*}"
        
        file_name_generic="${file_name_grib%.*}"
        file_name_generic=${file_name_generic/'fdk'/'%DOMAIN'}
        
        file_name_tmp_step1=${file_name_generic/'%DOMAIN'/$str_tmp_step1}'.nc'
        file_name_tmp_step2=${file_name_generic/'%DOMAIN'/$str_tmp_step2}'.nc'
        file_name_nc=${file_name_generic/'%DOMAIN'/$str_nc}'.nc'
        file_name_gzip=${file_name_generic/'%DOMAIN'/$str_nc}'.nc.gz'
        
	    file_path_zip=${data_folder_get}${file_name_zip}
	    file_path_grib=${data_folder_get}${file_name_grib}
	    file_path_tmp_step1=${data_folder_get}${file_name_tmp_step1}
	    file_path_tmp_step2=${data_folder_get}${file_name_tmp_step2}
	    file_path_nc=${data_folder_get}${file_name_nc}
	    file_path_gzip=${data_folder_get}${file_name_gzip}
	    # ----------------------------------------------------------------------------------------
	    
        # ----------------------------------------------------------------------------------------
        # Flag to check nc file creation
        create_nc=true
        # ----------------------------------------------------------------------------------------

	    # ----------------------------------------------------------------------------------------
	    # Create nc file over selected domain
	    echo " ====> CREATE NC FILE: ${file_path_gzip} ..."
	    if ! [ -e ${file_path_gzip} ]; then
	        
	        # ----------------------------------------------------------------------------------------
	        # Unzip file (from gz to grib)
	        echo -n " =====> UNZIP FILE: ${file_name_zip} ..."
	        if ! [ -e ${file_path_grib} ]; then
	            if gunzip -k $file_path_zip > /dev/null 2>&1; then
                    echo " DONE!"
                else
                    echo " FAILED! Error in command execution!"
                    create_nc=false
                fi
		    else
			    echo " SKIPPED! File previously unzipped!"
		    fi
	        # ----------------------------------------------------------------------------------------
	         
	        # ----------------------------------------------------------------------------------------
	        # Convert file to grib to netcdf fulldisk
	        echo -n " =====> CONVERT FILE: ${file_path_grib} to ${file_name_tmp_step1} ..."
	        if ! [ -e ${file_path_tmp_step1} ]; then
	        
	            if ${wgrib2_exec} ${file_path_grib} -netcdf ${file_path_tmp_step1} > /dev/null 2>&1; then
                    echo " DONE!"
                else
                    echo " FAILED! Error in command execution!"
                    create_nc=false
                fi

		    else
			    echo " SKIPPED! File previously converted!"
		    fi
	        # ----------------------------------------------------------------------------------------
	        
	        # ----------------------------------------------------------------------------------------
	        # Reduce file from netcdf to netcdf with dropping varible(s)
	        echo " =====> REDUCE AND RENAME FILE VARIABLE(S): ${file_name_tmp_step1} to ${file_name_tmp_step2} ..."
	        if ! [ -e ${file_path_tmp_step2} ]; then
	        
	            if ${ncks_exec} -C -x -v ${list_var_drop} ${file_path_tmp_step1} ${file_path_tmp_step2} > /dev/null 2>&1; then
                    echo " ... REDUCING VARIABLE DONE!"
                else
                    echo " ... REDUCING VARIABLE FAILED! Error in command execution!"
                    create_nc=false
                fi
                
                if ${ncrename_exec} -h -O -v ${var_rename_1} ${file_path_tmp_step2} > /dev/null 2>&1; then
                    echo " ... RENAMING VAR-1 DONE!"
                else
                    echo " ... RENAMING VAR-1 FAILED! Error in renaming variable 1!"
                    create_nc=false
                fi
                
                if ${ncrename_exec} -h -O -v ${var_rename_2} ${file_path_tmp_step2} > /dev/null 2>&1; then
                    echo " ... RENAMING VAR-2 DONE!"
                else
                    echo " ... RENAMING VAR-2 FAILED! Error in renaming variable 2!"
                    create_nc=false
                fi
                        
		    else
			    echo " SKIPPED! File variable(s) previously reduced!"
		    fi
		    # ----------------------------------------------------------------------------------------
	        
	        # ----------------------------------------------------------------------------------------
	        # Select file over domain
	        echo -n " =====> SELECT FILE OVER DOMAIN: ${file_name_tmp_step2} to ${file_name_nc} ..."
            if ! [ -e ${file_path_nc} ]; then
                
                if ${cdo_exec} sellonlatbox,${domain_bb} ${file_path_tmp_step2} ${file_path_nc} > /dev/null 2>&1; then
                    echo " DONE!"
                else
                    echo " FAILED! Error in command execution!"
                    create_nc=false
                fi
  
	        else
		        echo " SKIPPED! File previously selected over domain!"
	        fi
	        # ----------------------------------------------------------------------------------------
	        
	        # ----------------------------------------------------------------------------------------
	        # Check file nc 
	        echo -n " =====> CHECK AND COMPRESS FILE NC: ${file_name_nc} ..."
	        if [ "$create_nc" = true ] ; then
	            gzip ${file_path_nc}
	            echo " PASS!"
            else
                echo " FAILED! Errors occurred in nc file creation!"
        	    if [ -e ${file_path_nc} ]; then
	                rm ${file_path_nc} 
                fi
                create_nc=false
            fi
	        # ----------------------------------------------------------------------------------------
	        
	    else
	        # ----------------------------------------------------------------------------------------
	        # Exit with no operatio(s)
		    echo " SKIPPED! File previously created!"
		    # ----------------------------------------------------------------------------------------
	    fi  
	    # ----------------------------------------------------------------------------------------
	    
	    # ----------------------------------------------------------------------------------------
	    # Remove tmp file(s)
	    if [ -e ${file_path_grib} ]; then
	        rm ${file_path_grib} 
        fi
	    
	    if [ -e ${file_path_tmp_step1} ]; then
	        rm ${file_path_tmp_step1} 
        fi
	    
	    if [ -e ${file_path_tmp_step2} ]; then
	        rm ${file_path_tmp_step2} 
        fi
        
	    if [ -e ${file_path_nc} ]; then
	        rm ${file_path_nc} 
        fi
	    # ----------------------------------------------------------------------------------------
	    
	    # ----------------------------------------------------------------------------------------
	    # Exit message
	    if [ "$create_nc" = true ] ; then
            echo " ====> CREATE NC FILE: ${file_name_nc} ...  DONE!"
        else
            echo " ====> CREATE NC FILE: ${file_name_nc} ...  FAILED!"
        fi
	    # ----------------------------------------------------------------------------------------
	    
	done
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Info time end
	echo " ===> TIME_STEP: "$date_step" ===> END "
    # ----------------------------------------------------------------------------------------

done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

