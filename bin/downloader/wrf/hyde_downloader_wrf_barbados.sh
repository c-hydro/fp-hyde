#!/bin/bash -e

date_product="2018-07-10 00:00"

remote_folder_raw="/share/ddsData/WRF-regrid-3/Native/%YYYY/%MM/%DD/%HH00/"
local_folder_raw="/home/fabio/Documents/Working_Area/Code_Development/Workspace/PyCharm_Workspace_Python3/fp-ws/dynamic/input/%YYYY/%MM/%DD/%HH00/"

date_product=$(date -d "$date_product" '+%Y-%m-%d %H:%M')
year_product=$(date -u -d "$date_product" +"%Y")
month_product=$(date -u -d "$date_product" +"%m")
day_product=$(date -u -d "$date_product" +"%d")
hour_product=$(date -u -d "$date_product" +"%H")

remote_folder=${remote_folder_raw/'%YYYY'/$year_product}
remote_folder=${remote_folder/'%MM'/$month_product}
remote_folder=${remote_folder/'%DD'/$day_product}
remote_folder=${remote_folder/'%HH'/$hour_product}

local_folder=${local_folder_raw/'%YYYY'/$year_product}
local_folder=${local_folder/'%MM'/$month_product}
local_folder=${local_folder/'%DD'/$day_product}
local_folder=${local_folder/'%HH'/$hour_product}

if [ ! -d "$local_folder" ]; then
	mkdir -p $local_folder
fi

echo " ============================================================================== "
echo " Get WRF data (Time: $date_product) ... "
echo " Remote folder: $remote_folder"
echo " Local folder: $local_folder"

scp -r -P 20022  root@63.175.159.27:$remote_folder $local_folder

echo " Get WRF data (Time: $date_product) ... DONE!"
echo " ============================================================================== "
