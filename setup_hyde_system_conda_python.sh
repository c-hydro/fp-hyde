#!/usr/bin/env bash
set -euo pipefail

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE ENVIRONMENT - PYTHON LIBRARIES FOR PACKAGE - RUNNER TYPE - CONDA'
script_version="1.7.2"
script_date='2025/10/21'
#-----------------------------------------------------------------------------------------

# Miniconda installer (kept from your base script)
fp_env_file_miniconda='https://repo.continuum.io/miniconda/Miniconda3-py310_25.7.0-2-Linux-x86_64.sh'  # python 3.10

# Argument(s) default definition(s)
fp_env_tag_default='hyde_runner'

fp_env_folder_root_default='./conda/'
fp_env_file_reference_default='%ENV_TAG_settings'
fp_env_folder_libraries_default='%ENV_TAG_libraries'

fp_env_file_requirements_default='requirements_%ENV_TAG.yaml'

#-----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> $script_name (Version: $script_version Release_Date: $script_date)"
echo " ==> START ..."

script_args_n=$#
script_args_values=${*:-}

echo ""
echo " ==> Script arguments number: $script_args_n"
echo " ==> Script arguments values: $script_args_values"
echo ""
echo " ==> ARGS DEFINED:"
echo " ==> 1 - Tag of virtual environment [string: path] -> ${1:-<default>}"
echo " ==> 2 - Directory of libraries (conda root) [string: path] -> ${2:-<default>}"
echo " ==> 3 - Filename of system environment [string: filename] -> ${3:-<default>}"
echo " ==> 4 - Name of virtual environment [string: name] -> ${4:-<default>}"
echo " ==> 5 - Requirements YAML [string: name] -> ${5:-<default>}"
echo ""

# Parse args
if   [ $# -eq 0 ]; then
  fp_env_tag=$fp_env_tag_default
  fp_env_folder_root=$fp_env_folder_root_default
  fp_env_file_reference=$fp_env_file_reference_default
  fp_env_folder_libraries=$fp_env_folder_libraries_default
  fp_env_file_requirements=$fp_env_file_requirements_default
elif [ $# -eq 1 ]; then
  fp_env_tag=$1
  fp_env_folder_root=$fp_env_folder_root_default
  fp_env_file_reference=$fp_env_file_reference_default
  fp_env_folder_libraries=$fp_env_folder_libraries_default
  fp_env_file_requirements=$fp_env_file_requirements_default
elif [ $# -eq 2 ]; then
  fp_env_tag=$1
  fp_env_folder_root=$2
  fp_env_file_reference=$fp_env_file_reference_default
  fp_env_folder_libraries=$fp_env_folder_libraries_default
  fp_env_file_requirements=$fp_env_file_requirements_default
elif [ $# -eq 3 ]; then
  fp_env_tag=$1
  fp_env_folder_root=$2
  fp_env_file_reference=$3
  fp_env_folder_libraries=$fp_env_folder_libraries_default
  fp_env_file_requirements=$fp_env_file_requirements_default
elif [ $# -eq 4 ]; then
  fp_env_tag=$1
  fp_env_folder_root=$2
  fp_env_file_reference=$3
  fp_env_folder_libraries=$4
  fp_env_file_requirements=$fp_env_file_requirements_default
elif [ $# -eq 5 ]; then
  fp_env_tag=$1
  fp_env_folder_root=$2
  fp_env_file_reference=$3
  fp_env_folder_libraries=$4
  fp_env_file_requirements=$5
fi

# Expand placeholders
fp_env_folder_root="${fp_env_folder_root/'%ENV_TAG'/$fp_env_tag}"
fp_env_file_reference="${fp_env_file_reference/'%ENV_TAG'/$fp_env_tag}"
fp_env_folder_libraries="${fp_env_folder_libraries/'%ENV_TAG'/$fp_env_tag}"
fp_env_file_requirements="${fp_env_file_requirements/'%ENV_TAG'/$fp_env_tag}"

echo ""
echo " ==> ARGS SELECTED:"
echo " ==> 1 - Tag -> ${fp_env_tag}"
echo " ==> 2 - Conda root -> ${fp_env_folder_root}"
echo " ==> 3 - Env file -> ${fp_env_file_reference}"
echo " ==> 4 - Conda env name -> ${fp_env_folder_libraries}"
echo " ==> 5 - Requirements YAML -> ${fp_env_file_requirements}"
echo ""

#-----------------------------------------------------------------------------------------
# Check/install Miniconda  (installer creates the folder; we do NOT pre-create or delete it)
echo " ====> CHECK PYTHON ENVIRONMENT ... "
if [ -x "$fp_env_folder_root/bin/conda" ]; then
  echo " ====> FOUND EXISTING CONDA INSTALLATION."
  fp_env_install=false
else
  echo " ====> NO EXISTING CONDA FOUND. INSTALLING ..."
  fp_env_install=true
fi

if $fp_env_install; then
  echo " =====> DOWNLOADING MINICONDA INSTALLER ..."
  rm -f miniconda.sh
  wget -q "$fp_env_file_miniconda" -O miniconda.sh
  echo " =====> RUNNING INSTALLER ..."
  bash miniconda.sh -b -p "$fp_env_folder_root"
  echo " =====> CONDA INSTALLED SUCCESSFULLY."
else
  echo " =====> SKIPPING INSTALL (ALREADY EXISTS)."
fi

#-----------------------------------------------------------------------------------------
# Initialize conda for this shell
# shellcheck disable=SC1091
source "$fp_env_folder_root/etc/profile.d/conda.sh"
export PATH="$fp_env_folder_root/bin:$PATH"

#-----------------------------------------------------------------------------------------
# Install python libraries / Create or update the environment
echo " ====> INSTALL PYTHON LIBRARIES ... "

if [ -n "${fp_env_file_requirements:-}" ] && [ -f "$fp_env_file_requirements" ]; then
  echo " =====> USING REQUIREMENTS YAML: $fp_env_file_requirements"
  # Try to create; if env exists, update it
  conda env create -f "$fp_env_file_requirements" || conda env update -n "$fp_env_folder_libraries" -f "$fp_env_file_requirements"
  conda activate "$fp_env_folder_libraries"
else
  echo " =====> NO YAML FOUND: creating environment manually from conda-forge (strict) ..."
  conda create -y -n "$fp_env_folder_libraries" -c conda-forge \
    "python=3.10" "pip" \
    "numpy" "scipy" "pandas" "xarray" "matplotlib" "bottleneck" "dask" "cython" \
    "rasterio>=1.3,<1.4" "gdal>=3.9,<3.10" \
    "proj" "geos" "geotiff" "libnetcdf" "netcdf4" "hdf5" "hdf4" \
    "kealib" "tiledb" "openjpeg" "zstd" "libcurl" "libzip"
  conda activate "$fp_env_folder_libraries"
  # Pure-Python extras via pip (safe wheels)
  pip install --no-input cfgrib pyresample repurpose
fi

# Enforce strict conda-forge inside the env for ABI stability (GDAL/NetCDF/Rasterio)
conda config --env --add channels conda-forge
conda config --env --set channel_priority strict

# Optional sanity check (non-fatal)
python - <<'PY' || true
try:
    import rasterio, netCDF4
    print("Rasterio OK, GDAL:", getattr(rasterio, "__gdal_version__", "unknown"))
    print("netCDF4 OK, libnetcdf:", netCDF4.__netcdf4libversion__)
except Exception as e:
    print("Sanity check warning:", e)
PY

echo " ====> INSTALL PYTHON LIBRARIES ... DONE!"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Create environmental file (activation helper)
echo " ====> CREATE ENVIRONMENTAL FILE ... "
cd "$fp_env_folder_root"

[ -f "$fp_env_file_reference" ] && rm -f "$fp_env_file_reference"

{
  echo "PATH=$fp_env_folder_root/bin:"'$PATH'
  echo "export PATH"
  echo "source \"$fp_env_folder_root/etc/profile.d/conda.sh\""
  echo "conda activate $fp_env_folder_libraries"
} >> "$fp_env_file_reference"

echo " ====> ENVIRONMENTAL FILE CREATED: $fp_env_file_reference"
#-----------------------------------------------------------------------------------------

# Info script end
echo " ==> $script_name (Version: $script_version Release_Date: $script_date)"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="

