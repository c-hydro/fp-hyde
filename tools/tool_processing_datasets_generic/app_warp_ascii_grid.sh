#!/bin/bash -e

dem_ascii_in='barbados.dem.gcp.txt'
dem_tiff_in='barbados.dem.gcp.tif'
dem_tiff_out='barbados.dem.out.tif'
dem_ascii_out='barbados.dem.out.txt'

dem_step_out=0.0009
interp_method='near'

gdal_translate -of "GTiff" $dem_ascii_in $dem_tiff_in

gdalwarp -tr $dem_step_out $dem_step_out -r $interp_method $dem_tiff_in $dem_tiff_out

gdal_translate -of "AAIGrid" $dem_tiff_out $dem_ascii_out


