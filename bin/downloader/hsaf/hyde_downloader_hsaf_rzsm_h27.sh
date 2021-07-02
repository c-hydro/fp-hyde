#!/bin/bash -e

# ----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DOWNLOADER - HSAF PRODUCT SOIL MOISTURE RZSM - H27'
script_version="1.5.0"
script_date='2019/10/04'

# Script argument(s)
days=4000
proxy=""

ftp_url=""
ftp_usr=""
ftp_pwd=""

ftp_folder_raw="" # archive h27

# Define folder(s)
folder_in_raw="/home/hsaf/hsaf_datasets/dynamic/source/h27/%YYYY/%MM/%DD/"
folder_out_raw="/home/hsaf/hsaf_datasets/dynamic/source/rzsm/%YYYY/%MM/%DD/"
folder_grid="/home/hsaf/hsaf_datasets/static/soil_moisture/gridded/mod_rzsm/nrt/grid_domain/h27/"

# Define filename(s)
file_in_grib_raw="h27_%YYYY%MM%DD00_T1279.grib"
file_out_grib_raw="rzsm_%YYYY%MM%DD%HH00_global.grib"

file_in_nc_raw="rzsm_%YYYY%MM%DD%HH00_global.nc"
file_tmp_nc_raw="rzsm_%YYYY%MM%DD%HH00_tmp.nc"
file_out_nc_raw="rzsm_%YYYY%MM%DD%HH00_europe.nc"

file_grid='rzsm_grid_europe.nc'

file_ref_grid_nc="reference_file.h14.nc" # file for h14 20130701 created by h14 downloader procedure renamed
file_ref_grid_ascii="reference_grid.h14.txt"

# Define domain bounding box
domain_bb='-15,30,30,60'
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Define executable(s)
# exec_cdo="/home/fabio/Desktop/Apps/cdo-1.9.6_NC-4.6.0_HDF-1.8.17_ECCODES-2.12.5/bin/cdo" # local
exec_cdo="/home/hsaf/library/cdo-1.7.2rc3_NC-4.1.2_HDF-1.8.17/bin/cdo" # server
exec_ncap2="ncap2"
exec_ncks="ncks"
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Export library path dependecies
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/hsaf/library/grib_api-1.15.0/lib/
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Get time
# time_now=$(date '+%Y-%m-%d 00:00')
time_now='2013-06-30 00:00' # DEBUG
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
	time_step=$(date -d "$time_now ${day} days ago" +'%Y%m%d%H%M')

    year_step=${time_step:0:4}
    month_step=${time_step:4:2}
    day_step=${time_step:6:2}
    hour_step=${time_step:8:2}
    minute_step=${time_step:10:2}

	ftp_time_step=${year_step}${month_step}${day_step}_${hour_step}${minute_step}
	
    # Info time startexport LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/hsaf/library/grib_api-1.15.0/lib/
    echo " ===> TIME_STEP: "$time_step" ===> START "
	# ----------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------
	# Define dynamic folder(s)
    ftp_folder_step=${ftp_folder_raw//'%YYYY'/$year_step}
    ftp_folder_step=${ftp_folder_step/'%MM'/$month_step}
    ftp_folder_step=${ftp_folder_step/'%DD'/$day_step}
    ftp_folder_step=${ftp_folder_step/'%HH'/$hour_step}
	ftp_folder_step=${ftp_folder_step/'%MM'/$minute_step}
	
	folder_in_step=${folder_in_raw/'%YYYY'/$year_step}
    folder_in_step=${folder_in_step/'%MM'/$month_step}
    folder_in_step=${folder_in_step/'%DD'/$day_step}
    folder_in_step=${folder_in_step/'%HH'/$hour_step}
	folder_in_step=${folder_in_step/'%MM'/$minute_step}

	file_in_grib_step=${file_in_grib_raw/'%YYYY'/$year_step}
	file_in_grib_step=${file_in_grib_step/'%MM'/$month_step}
	file_in_grib_step=${file_in_grib_step/'%DD'/$day_step}
	file_in_grib_step=${file_in_grib_step/'%HH'/$hour_step}
	file_in_grib_step=${file_in_grib_step/'%MM'/$minute_step}

	# Path(s) definition
	path_in_step=${folder_in_step}${file_in_grib_step}
	
	path_grid=${folder_grid}${file_grid}
	path_ref_grid_nc=${folder_grid}${file_ref_grid_nc}
	path_ref_grid_ascii=${folder_grid}${file_ref_grid_ascii}
	# ----------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------	
	# Create folder(s)
	if [ ! -d "$folder_in_step" ]; then
		mkdir -p $folder_in_step
	fi
	if [ ! -d "$folder_grid" ]; then
		mkdir -p $folder_grid
	fi
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Condition to control file availability 
	if ! [ -e ${path_in_step} ]; then

		# ----------------------------------------------------------------------------------------
		# Get file list from ftp
		ftp_file_list=`lftp << ftprem
						set ftp:proxy ${proxy}
						open -u ${ftp_usr},${ftp_pwd} ${ftp_url}
						cd ${ftp_folder_step}
						cls -1 | sort -r | grep ${ftp_time_step} | sed -e "s/@//"
						close
						quit
ftprem`
		# ----------------------------------------------------------------------------------------
    
		# ----------------------------------------------------------------------------------------
		# Download file(s)	
		for ftp_file in ${ftp_file_list}; do
		    
		    echo -n " ====> DOWNLOAD FILE: ${ftp_file} IN ${folder_in_step} ..." 
		    
			if ! [ -e ${folder_in_step}/${ftp_file} ]; then
				
				`lftp << ftprem
					        set ftp:proxy  ${proxy}
							open -u ${ftp_usr},${ftp_pwd} ${ftp_url}
							cd ${ftp_folder_step}
							get1 -o ${folder_in_step}/${ftp_file} ${ftp_file}
							close
							quit
ftprem`

				if [ $? -eq 0 ] > /dev/null 2>&1; then
			 		echo " DONE!"
				else
					echo " FAILED [FTP ERROR]!"
				fi
			
			else
				echo " SKIPPED! File previously downloaded!"
			fi
		    # ----------------------------------------------------------------------------------------
        
		done
		# ----------------------------------------------------------------------------------------
	
	fi
    # ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Iterate on file(s) in source folder
	for path_in_raw in "$folder_in_step"/*; do
		
		# ----------------------------------------------------------------------------------------
		# Condition to control file extention (permitted only .bz2)
		if [[ $path_in_raw == *.grib ]]; then
			
			# ----------------------------------------------------------------------------------------
			# Get filename and folder		
			file_in_raw=$(basename -- "$path_in_raw")
			#folder_in_raw=$(dirname -- "$path_in_raw")
			# ----------------------------------------------------------------------------------------

			# ----------------------------------------------------------------------------------------
			# Time file information
			time_file=$(echo ${file_in_raw} | grep -Eo '[[:digit:]]{4}[[:digit:]]{2}[[:digit:]]{2}[[:digit:]]{2}')
			
			year_step=${time_file:0:4}
			month_step=${time_file:4:2}
			day_step=${time_file:6:2}
			hour_step=${time_file:8:2}
			
			# Path(s) file information
			folder_in_step=${folder_in_raw/'%YYYY'/$year_step}
			folder_in_step=${folder_in_step/'%MM'/$month_step}
			folder_in_step=${folder_in_step/'%DD'/$day_step}
			folder_in_step=${folder_in_step/'%HH'/$hour_step}
			folder_in_step=${folder_in_step/'%MM'/$minute_step}
			
			folder_out_step=${folder_out_raw/'%YYYY'/$year_step}
			folder_out_step=${folder_out_step/'%MM'/$month_step}
			folder_out_step=${folder_out_step/'%DD'/$day_step}
			folder_out_step=${folder_out_step/'%HH'/$hour_step}

			file_in_grib_step=${file_in_grib_raw/'%YYYY'/$year_step}
			file_in_grib_step=${file_in_grib_step/'%MM'/$month_step}
			file_in_grib_step=${file_in_grib_step/'%DD'/$day_step}
			file_in_grib_step=${file_in_grib_step/'%HH'/$hour_step}

			file_out_grib_step=${file_out_grib_raw/'%YYYY'/$year_step}
			file_out_grib_step=${file_out_grib_step/'%MM'/$month_step}
			file_out_grib_step=${file_out_grib_step/'%DD'/$day_step}
			file_out_grib_step=${file_out_grib_step/'%HH'/$hour_step}

			file_in_nc_step=${file_in_nc_raw/'%YYYY'/$year_step}
			file_in_nc_step=${file_in_nc_step/'%MM'/$month_step}
			file_in_nc_step=${file_in_nc_step/'%DD'/$day_step}
			file_in_nc_step=${file_in_nc_step/'%HH'/$hour_step}

			file_tmp_nc_step=${file_tmp_nc_raw/'%YYYY'/$year_step}
			file_tmp_nc_step=${file_tmp_nc_step/'%MM'/$month_step}
			file_tmp_nc_step=${file_tmp_nc_step/'%DD'/$day_step}
			file_tmp_nc_step=${file_tmp_nc_step/'%HH'/$hour_step}

			file_out_nc_step=${file_out_nc_raw/'%YYYY'/$year_step}
			file_out_nc_step=${file_out_nc_step/'%MM'/$month_step}
			file_out_nc_step=${file_out_nc_step/'%DD'/$day_step}
			file_out_nc_step=${file_out_nc_step/'%HH'/$hour_step}

			# Path(s) definition
			path_in_grib_step=${folder_in_step}/${file_in_grib_step}
			path_out_grib_step=${folder_in_step}/${file_out_grib_step}
			path_in_nc_step=${folder_out_step}/${file_in_nc_step}
			path_tmp_nc_step=${folder_out_step}/${file_tmp_nc_step}
			path_out_nc_step=${folder_out_step}/${file_out_nc_step}
			# ----------------------------------------------------------------------------------------
			
			# ----------------------------------------------------------------------------------------	
			# Create folder(s)
			if [ ! -d "$folder_in_step" ]; then
				mkdir -p $folder_in_step
			fi
			if [ ! -d "$folder_out_step" ]; then
				mkdir -p $folder_out_step
			fi
			# ----------------------------------------------------------------------------------------

			# ----------------------------------------------------------------------------------------
			# Create file grid
			if [ -e ${path_ref_grid_nc} ]; then
				echo " =====> CREATE GRID REFERENCE: ${file_ref_grid_ascii} ... "
				if ! [ -e ${path_ref_grid_ascii} ]; then
					
				    if ${exec_cdo} griddes $path_ref_grid_nc > $path_ref_grid_ascii 2>&1; then
				        echo " DONE!"
				    else
				        echo " ERROR! Error in command execution!"
						exit
				    fi					
				fi
			else
				echo " ERROR! grid reference file not available!"
				exit
			fi
			# ----------------------------------------------------------------------------------------

			# ----------------------------------------------------------------------------------------
			# Create nc file over selected domain
			echo " ====> CREATE NC FILE: ${file_out_nc_step} ..."
			if ! [ -e ${path_out_nc_step} ]; then

				# ----------------------------------------------------------------------------------------
				# Set regular grid to file
				echo -n " =====> SET REGULAR GRID TO FILE: ${file_in_grib_step} to ${file_out_grib_step} ..."
				if ! [ -e ${path_out_grib_step} ]; then

				    if $exec_cdo -R copy $path_in_grib_step $path_out_grib_step > /dev/null 2>&1; then
				        echo " DONE!"
				    else
				        echo " FAILED! Error in command execution!"
				    fi

				else
					echo " SKIPPED! grid previously set!"
				fi
				# ----------------------------------------------------------------------------------------

				# ----------------------------------------------------------------------------------------
				# Convert file to grib to netcdf fulldisk
				echo -n " =====> CONVERT FILE: ${file_out_grib_step} to ${file_in_nc_step} ..."
				if ! [ -e ${path_in_nc_step} ]; then
				
				    if $exec_cdo -f nc copy $path_out_grib_step $path_in_nc_step > /dev/null 2>&1; then
				        echo " DONE!"
				    else
				        echo " FAILED! Error in command execution!"
				    fi

				else
					echo " SKIPPED! File previously converted!"
				fi
				# ----------------------------------------------------------------------------------------		
				
				# ----------------------------------------------------------------------------------------
				# Compute VAR_0_7 ==> Equation: float(7)/float(7)*H14_SM_V_L1
				echo -n " =====> COMPUTE SOIL MOISTURE VAR 0_7 ..."
				if [ -e ${path_in_nc_step} ]; then
				
				    if ${exec_ncap2} -s "var_0_7=1*var40" -v -A $path_in_nc_step $path_in_nc_step > /dev/null 2>&1; then
				        echo " DONE!"
				    else
				        echo " FAILED! Error in command execution!"
				    fi

				else
					echo " FAILED! File does not exist! Variable was not computed!"
				fi
				# ----------------------------------------------------------------------------------------	
				
				# ----------------------------------------------------------------------------------------
				# Compute VAR_0_28 ==> Equation: float(7)/float(28)*H14_SM_V_L1 + float(28-7)/float(28)*H14_SM_V_L2
				echo -n " =====> COMPUTE SOIL MOISTURE VAR 0_28 ..."
				if [ -e ${path_in_nc_step} ]; then
				
				    if ${exec_ncap2} -s "var_0_28=0.25*var40 + 0.75*var41" -v -A $path_in_nc_step $path_in_nc_step > /dev/null 2>&1; then
				        echo " DONE!"
				    else
				        echo " FAILED! Error in command execution!"
				    fi

				else
					echo " FAILED! File does not exist! Variable was not computed!"
				fi
				# ----------------------------------------------------------------------------------------	
				
				# ----------------------------------------------------------------------------------------
				# Compute VAR_0_100 ==> Equation: float(7)/float(100)*H14_SM_V_L1 + float(28-7)/float(100)*H14_SM_V_L2 + (float(100-7-(28-7))/float(100))*H14_SM_V_L3
				echo -n " =====> COMPUTE SOIL MOISTURE VAR 0_100 ..."
				if [ -e ${path_in_nc_step} ]; then
				
				    if ${exec_ncap2} -s "var_0_100=0.07*var40 + 0.21*var41 + 0.72*var42" -v -A $path_in_nc_step $path_in_nc_step > /dev/null 2>&1; then
				        echo " DONE!"
				    else
				        echo " FAILED! Error in command execution!"
				    fi

				else
					echo " FAILED! File does not exist! Variable was not computed!"
				fi
				# ----------------------------------------------------------------------------------------	
				
				# ----------------------------------------------------------------------------------------
				# Select file over domain
				echo -n " =====> SELECT FILE OVER DOMAIN: ${file_in_nc_step} to ${file_out_nc_step} ..."
				if ! [ -e ${path_out_nc_step} ]; then
				
				    if ${exec_cdo} sellonlatbox,${domain_bb} ${path_in_nc_step} ${path_tmp_nc_step} > /dev/null 2>&1; then
				        echo " DONE!"
				    else
				        echo " FAILED! Error in command execution!"
				    fi
				    
				else
					echo " SKIPPED! File previously selected over domain!"
				fi
				# ----------------------------------------------------------------------------------------	
				
				# ----------------------------------------------------------------------------------------
				# Regrid data over grid reference
				echo -n " =====> REGRID DATA OVER GRID REFERENCE: ${file_tmp_nc_step} to ${file_out_nc_step} ..."
				if ! [ -e ${path_out_nc_step} ]; then
				
				    if ${exec_cdo} remapnn,$path_ref_grid_ascii $path_tmp_nc_step $path_out_nc_step > /dev/null 2>&1; then
				        echo " DONE!"
				    else
				        echo " FAILED! Error in command execution!"
				    fi
				    
				else
					echo " SKIPPED! File previously mapped over grid reference!"
				fi
				# ----------------------------------------------------------------------------------------			
			
			else
			    # ----------------------------------------------------------------------------------------ù
			    # Exit with no operatio(s)
				echo " SKIPPED! File previously created!"
				# ----------------------------------------------------------------------------------------
			fi  
			# ----------------------------------------------------------------------------------------
			
			# ----------------------------------------------------------------------------------------
			# Create file grid
			if [ -e ${path_out_nc_step} ]; then
				echo " =====> CREATE GRID FILE: ${file_grid} ... "
				if ! [ -e ${path_grid} ]; then
					
				    if ${exec_ncks} -v lon,lat ${path_out_nc_step} ${path_grid} > /dev/null 2>&1; then
				        echo " DONE!"
				    else
				        echo " FAILED! Error in command execution!"
				    fi					
				fi
			fi
			# ----------------------------------------------------------------------------------------

			# ----------------------------------------------------------------------------------------
			# Remove tmp file(s)
			if [ -e ${path_out_grib_step} ]; then
			    rm ${path_out_grib_step} 
		    fi
		    
			if [ -e ${path_in_nc_step} ]; then
			    rm ${path_in_nc_step} 
		    fi
			
			if [ -e ${path_tmp_nc_step} ]; then
			    rm ${path_tmp_nc_step} 
		    fi
			# ----------------------------------------------------------------------------------------

			# ----------------------------------------------------------------------------------------
			# Exit message
			if [ -e ${path_out_nc_step} ]; then
				echo " ====> CREATE NC FILE: ${file_out_nc_step} ... DONE!"
			else
				echo " ====> CREATE NC FILE: ${file_out_nc_step} ... FAILED!"
			fi
			# ----------------------------------------------------------------------------------------
				
		fi
		# ----------------------------------------------------------------------------------------
		
	done
	# ----------------------------------------------------------------------------------------
	
	# Info time end
	echo " ===> TIME_STEP: $time_step ===> END "
    # ----------------------------------------------------------------------------------------

done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------









