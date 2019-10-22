#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='FP UTILS - CLEANER EMPTY SUBFOLDER(S)'
script_version="1.0.0"
script_date='2018/07/26'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
main_folder='/home/hsaf/hsaf_datasets/dynamic/ancillary/'
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."

find $main_folder -depth -empty -type d -exec rmdir {} \;

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------
