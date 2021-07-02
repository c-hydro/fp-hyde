#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE UTILS - CLEANER FOLDER(S)'
script_version="1.5.0"
script_date='2019/10/16'
#-----------------------------------------------------------------------------------------

#----------------------------------------------------------------------------------------
# Select hour for removing data daily
hour_remove_daily=21

folder_list_name=("/share/c-hydro/lock/" "/share/c-hydro/run/obs_ws_realtime/")
folder_list_remove=('daily' 'hourly') # Allowed flag [daily, hourly]
folder_list_make=(true false)
#----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get information (-u to get gmt time)
time_system=$(date +"%Y-%m-%d %H:00")
# time_system=$(date -u +"%Y-%m-%d %H:00")
# time_system="2019-10-09 23:00"
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."

# Get hour system
hour_system=$(date +%H -d "$time_system")

# Info about time system
echo " ==> TimeSystem: "$time_system" HourSystem: "$hour_system

# Iterate over folder list
for ((i=0;i<${#folder_list_name[@]};++i)); do
	
	# ----------------------------------------------------------------------------------------
	# Folder information
	folder_name=${folder_list_name[i]}
	folder_remove=${folder_list_remove[i]}
	folder_make=${folder_list_make[i]}
	# ----------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------	
	# Remove folder starting info
	echo " ===> Remove folder $folder_name ... "
	
	# Check folder availability
	if [ -d "$folder_name" ]; then
		
		# Check removing type
		if [[ "$folder_remove" == "daily" ]]; then
			
			# Daily procedure
			echo " ====> Daily removing set to $hour_remove_daily ... "
			if [ "$hour_system" -eq $hour_remove_daily ]; then
				rm -r $folder_name
				echo " ====> Daily removing set to $hour_remove_daily hour ... DONE! "
			else
				echo " ====> Daily removing set to $hour_remove_daily hour ... SKIPPED! [hour_system: $hour_system] and [hour_remove: $hour_remove_daily] are different! "
			fi

		elif [[ "$folder_remove" == "hourly" ]]; then
			
			# Hourly procedure
			echo " ====> Hourly removing at $hour_system hour ... "
			rm -r $folder_name
			echo " ====> Hourly removing at $hour_system hour ... DONE"

		else
			# Not allowed procedure
			echo " ====>  Removing flag is not allowed. Check your flag!"
		fi
		
		# Remove folder ending info (success)
		echo " ===> Remove folder $folder_name ... DONE"
		
	else
		# Remove folder ending info (folder not available)
		echo " ===> Remove folder $folder_name ... SKIPPED. Folder not available!"
	fi
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Create folder starting info
	echo " ===> Create folder $folder_name ... "
	if $folder_make; then
		if [ ! -d "$folder_name" ]; then
			mkdir -p $folder_name
			echo " ===> Create folder $folder_name ... DONE"
		else
			echo " ===> Create folder $folder_name ... SKIPPED. Folder already exists!"	
		fi
	else
		echo " ===> Create folder $folder_name ... SKIPPED. Folder creation not activated!"	

	fi
	# ----------------------------------------------------------------------------------------

done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------




