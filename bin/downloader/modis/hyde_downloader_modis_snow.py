#!/usr/bin/python3

"""
MODIS Downloading Tool - MODIS SNOW

__date__ = '20191007'
__version__ = '1.0.1'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hyde'

General command line:
python3 hyde_downloader_modis_snow.py -settingfile configuration.json

Version:
20191007 (1.0.1) --> Hyde package refactor
20180906 (1.0.0) --> Beta release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import time
import datetime
import gzip

from shutil import rmtree, copyfileobj
from glob import glob
from subprocess import Popen, STDOUT, DEVNULL, PIPE
from os import makedirs, stat, chmod, remove, rename
from os.path import join, exists, isfile
from pandas import date_range
from argparse import ArgumentParser
from json import load
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
sAlgName = 'MODIS DOWNLOADING TOOL - MODIS SNOW'
sAlgVersion = '1.0.0'
sAlgRelease = '2018-09-06'
# Algorithm parameter(s)
sZipExt = '.gz'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Info algorithm
    print(' ============================================================================ ')
    print(' ==> ' + sAlgName + ' (Version: ' + sAlgVersion + ' Release_Date: ' + sAlgRelease + ')')
    print(' ==> START ... ')
    print(' ')

    # Time algorithm information
    dStartTime = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    with open(getSettings(), "r") as oFileSettings:
        oDataSettings = load(oFileSettings)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Define time information
    if oDataSettings['time_info']['time_get'] is None:
        sTime_GET = datetime.datetime.now().strftime('%Y%m%d')
    else:
        sTime_GET = oDataSettings['time_info']['time_get']

    oTime_STEPS = date_range(end=sTime_GET,
                             periods=oDataSettings['time_info']['time_period'],
                             freq=oDataSettings['time_info']['time_frequency'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over times
    for oTime_STEP in oTime_STEPS:

        # -------------------------------------------------------------------------------------
        # Select time step
        sTime_STEP = oTime_STEP.strftime('%Y.%m.%d')
        sYear_STEP = oTime_STEP.strftime('%Y')
        sMonth_STEP = oTime_STEP.strftime('%m')
        sDay_STEP = oTime_STEP.strftime('%d')
        sJDay_STEP = str(oTime_STEP.timetuple().tm_yday).zfill(3)

        # Info time
        print(' ===> TIME STEP: ' + sTime_STEP + ' [JD: ' + sJDay_STEP + ']')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Define tile(s)
        oTileName = []
        for sTileKey, oTileIdx in sorted(oDataSettings['data_info']['tiles'].items()):

            # Define tile string id
            sTileIdx_H = 'h' + str(oTileIdx['H']).zfill(2)
            sTileIdx_V = 'v' + str(oTileIdx['V']).zfill(2)
            sTileIdx = sTileIdx_H + sTileIdx_V

            oTileName.append(sTileIdx)
        sTileName = '_'.join(oTileName)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Zip extension
        if oDataSettings['data_info']['outcome']['zip'] is True:
            sZipExt_OUTCOME = sZipExt
        else:
            sZipExt_OUTCOME = ''
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Define data tags
        oData_TAGS = {'$product': oDataSettings['data_info']['product'],
                      '$version': oDataSettings['data_info']['version'],
                      '$tiles': sTileName,
                      '$time': sTime_STEP, '$yyyy': sYear_STEP, '$mm': sMonth_STEP, '$dd': sDay_STEP, '$jd': sJDay_STEP,
                      '$data_root': oDataSettings['http_info']['data_root'],
                      '$data_folder': oDataSettings['http_info']['data_folder']}
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Define TMP folder
        sFolder_TMP = setTags(oDataSettings['data_info']['temp']['folder'], oData_TAGS)
        deleteFolder(sFolder_TMP)
        makeFolder(sFolder_TMP)

        # Define DOWNLOAD, TILE, MOSAIC and RESEMPLE filename(s)
        sFileName_TMP_DWN_TILE = setTags(oDataSettings['data_info']['temp']['file_download_tile'], oData_TAGS)
        sFileName_TMP_MOS_TILE = setTags(oDataSettings['data_info']['temp']['file_mosaic_tiles'], oData_TAGS)
        sFileName_TMP_MOS_DATA = setTags(oDataSettings['data_info']['temp']['file_mosaic_data'], oData_TAGS)
        sFileName_TMP_RES_DATA = setTags(oDataSettings['data_info']['temp']['file_resample_data'], oData_TAGS)
        sFileName_TMP_RES_PARAMS = setTags(oDataSettings['data_info']['temp']['file_resample_parameters'], oData_TAGS)

        # Delete old file(s)
        deleteFile(join(sFolder_TMP, sFileName_TMP_DWN_TILE))
        deleteFile(join(sFolder_TMP, sFileName_TMP_MOS_TILE))
        deleteFile(join(sFolder_TMP, sFileName_TMP_MOS_DATA))
        deleteFile(join(sFolder_TMP, sFileName_TMP_RES_DATA))
        deleteFile(join(sFolder_TMP, sFileName_TMP_RES_PARAMS))
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Define SOURCE and OUTCOME folder(s)
        sFolder_SOURCE = setTags(oDataSettings['data_info']['source']['folder'], oData_TAGS)
        makeFolder(sFolder_SOURCE)
        sFolder_OUTCOME = setTags(oDataSettings['data_info']['outcome']['folder'], oData_TAGS)
        makeFolder(sFolder_OUTCOME)

        # Define SOURCE and OUTCOME filename(s)
        sFileName_SOURCE_DATA = setTags(oDataSettings['data_info']['source']['file'], oData_TAGS)
        sFileName_SOURCE_HTTP = setTags(oDataSettings['data_info']['source']['http'], oData_TAGS)
        sFileName_OUTCOME_DATA = setTags(oDataSettings['data_info']['outcome']['file'], oData_TAGS)
        sFileName_OUTCOME_ZIP = sFileName_OUTCOME_DATA + sZipExt_OUTCOME
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Algorithm flag(s)
        bFileName_SOURCE_DATA = oDataSettings['data_info']['flag']['source_data']
        bFileName_OUTCOME_DATA = oDataSettings['data_info']['flag']['outcome_data']
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Info data
        print(' ====> GET FILE: ' + sFileName_OUTCOME_DATA + ' ... ')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Check outcome data availability
        if ((not exists(join(sFolder_OUTCOME, sFileName_OUTCOME_DATA))) or
             (not exists(join(sFolder_OUTCOME, sFileName_OUTCOME_ZIP)))) or (bFileName_OUTCOME_DATA is True):

            # -------------------------------------------------------------------------------------
            # Iterate over tile(s)
            oFileTile = dict()
            oFileList = []
            for iTileID, sTileIdx in enumerate(sorted(oTileName)):

                # -------------------------------------------------------------------------------------
                # Info tile
                print(' =====> GET TILE: ' + sTileIdx + ' ... ')
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Define variable name
                sFileVar_SOURCE = oDataSettings['data_info']['product'] + '.' + oDataSettings['data_info']['version']
                # Define DWN_TILE, DATA and HTTP filename(s)
                sFileName_SOURCE_DATA_ID = sFileName_SOURCE_DATA.replace('$tile', sTileIdx)
                sFileName_SOURCE_HTTP_ID = sFileName_SOURCE_HTTP.replace('$tile', sTileIdx)
                sFileName_TMP_DWN_TILE_ID = sFileName_TMP_DWN_TILE.replace('$tile', sTileIdx)
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Test file availability
                sFileName_SOURCE_DATA_CPL = glob(sFolder_SOURCE + '*' + sTileIdx + '*.hdf')

                # Condition for activating file downloading
                if (not sFileName_SOURCE_DATA_CPL) or (bFileName_SOURCE_DATA is True):

                    # -------------------------------------------------------------------------------------
                    # Define downloader script
                    oFileLines = dict()
                    oFileLines[0] = str('#!/bin/bash') + '\n'

                    oFileLines[1] = str('touch .netrc') + '\n'
                    oFileLines[2] = str('echo "machine ' + oDataSettings['http_info']['website'] +
                                        ' login  ' + oDataSettings['http_info']['user'] +
                                        ' password ' + oDataSettings['http_info']['password'] +
                                        '" >> .netrc') + '\n'
                    oFileLines[3] = str('chmod 0600 .netrc') + '\n'
                    oFileLines[4] = str('touch .urs_cookies') + '\n'

                    oFileLines[5] = str('wget -P ' + sFolder_TMP)
                    oFileLines[5] += str(' --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies')
                    oFileLines[5] += str(' --keep-session-cookies --no-check-certificate --auth-no-challenge=on')
                    oFileLines[5] += str(' -r --reject "index.html*" -np -e robots=off')
                    oFileLines[5] += str(' --no-parent -A "' + sFileName_SOURCE_DATA_ID + '"')
                    oFileLines[5] += str(' ' + sFileName_SOURCE_HTTP_ID) + '\n'

                    oFileLines[6] = str('mv ' +
                                        join(sFolder_TMP,
                                             oDataSettings['http_info']['data_root'],
                                             oDataSettings['http_info']['data_folder'],
                                             sFileVar_SOURCE, sTime_STEP, sFileName_SOURCE_DATA_ID) + ' ' +
                                        sFolder_SOURCE)

                    # Open, write and close executable file
                    oFile = open(join(sFolder_TMP, sFileName_TMP_DWN_TILE_ID), 'w')
                    oFile.writelines(oFileLines.values())
                    oFile.close()
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Run bash executable file
                    makeExec(join(sFolder_TMP, sFileName_TMP_DWN_TILE_ID))
                    oProcExec = Popen(join(sFolder_TMP, sFileName_TMP_DWN_TILE_ID),)
                                      #stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
                    oProcExec.communicate()

                    # Get complete filename
                    oFileRetrieve = glob(sFolder_SOURCE + '*' + sTileIdx + '*.hdf')
                    if oFileRetrieve.__len__() > 0:
                        sFileName_SOURCE_DATA_CPL = glob(sFolder_SOURCE + '*' + sTileIdx + '*.hdf')[0]
                        # Info tile
                        print(' =====> GET TILE: ' + sTileIdx + ' ... DONE!')
                    elif oFileRetrieve.__len__() == 0:
                        sFileName_SOURCE_DATA_CPL = None
                        print(' =====> GET TILE: ' + sTileIdx + ' ... FAILED!')
                    # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # File previously downloaded, get filename only
                    sFileName_SOURCE_DATA_CPL = glob(sFolder_SOURCE + '*' + sTileIdx + '*.hdf')[0]
                    # Info tile
                    print(' =====> GET TILE: ' + sTileIdx + ' ... SKIPPED! Tile previously downloaded!')
                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Save complete filename
                if sFileName_SOURCE_DATA_CPL is not None:
                    oFileTile[sTileIdx] = sFileName_SOURCE_DATA_CPL + '\n'
                    oFileList.append(sFileName_SOURCE_DATA_CPL)
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check tile(s) availability
            if oFileList:

                # -------------------------------------------------------------------------------------
                # Tile data using mrt mosaic application
                print(' =====> MOSAICKING DATA ... ')
                if oDataSettings['mrt_info']['app_mosaic']['activation']:

                    # -------------------------------------------------------------------------------------
                    # Tile condition
                    if oFileTile.__len__() > 1:

                        # -------------------------------------------------------------------------------------
                        # Open and save file with tile(s) definition
                        oFile_TMP_MOS_TILE = open(join(sFolder_TMP, sFileName_TMP_MOS_TILE), 'w')
                        oFile_TMP_MOS_TILE.writelines(oFileTile.values())
                        oFile_TMP_MOS_TILE.close()
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Command line mosaicking
                        sLineCmd_MOS = (join(oDataSettings['mrt_info']['bin'], 'mrtmosaic') +
                                        ' -i ' + join(sFolder_TMP, sFileName_TMP_MOS_TILE) +
                                        ' -o ' + join(sFolder_TMP, sFileName_TMP_MOS_DATA))

                        # Execute mosaicking algorithm
                        oProcExec = Popen(sLineCmd_MOS, shell=True,
                                          stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
                        oProcExec.communicate()

                        # Info mosaicking
                        print(' =====> MOSAICKING DATA ... DONE!')
                        # -------------------------------------------------------------------------------------

                    else:
                        # -------------------------------------------------------------------------------------
                        # Tile data equal to 1 (only one file)
                        sFileName_TMP_MOS_TILE = oFileList[0]
                        rename(join(sFolder_TMP, sFileName_TMP_MOS_TILE), join(sFolder_TMP, sFileName_TMP_MOS_DATA))
                        # Info mosaicking
                        print(' =====> MOSAICKING DATA ... SKIPPED! Only one tile downloaded and available!')
                        # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Tile data not activated (only one tile)
                    sFileName_TMP_MOS_TILE = oFileList[0]
                    rename(join(sFolder_TMP, sFileName_TMP_MOS_TILE), join(sFolder_TMP, sFileName_TMP_MOS_DATA))
                    # Info mosaicking
                    print(' =====> MOSAICKING DATA ... NOT ACTIVATED!')
                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Resample data using mrt resample application
                print(' =====> RESAMPLING DATA ... ')
                if oDataSettings['mrt_info']['app_mosaic']['activation']:

                    # -------------------------------------------------------------------------------------
                    # Define resample file
                    oFileLines = dict()
                    oFileLines[0] = str('INPUT_FILENAME = ' +
                                        join(sFolder_TMP, sFileName_TMP_MOS_DATA)) + '\n'
                    oFileLines[1] = str('SPATIAL_SUBSET_TYPE = ' +
                                        oDataSettings['mrt_info']['app_resample']['special_subset']) + '\n'
                    oFileLines[2] = str('OUTPUT_FILENAME =  ' +
                                        join(sFolder_TMP, sFileName_TMP_RES_DATA)) + '\n'
                    oFileLines[3] = str('RESAMPLING_TYPE = ' +
                                        oDataSettings['mrt_info']['app_resample']['resampling_method']) + '\n'
                    oFileLines[4] = str('OUTPUT_PROJECTION_TYPE = ' +
                                        oDataSettings['mrt_info']['app_resample']['proj']) + '\n'
                    oFileLines[5] = str('DATUM =  ' +
                                        oDataSettings['mrt_info']['app_resample']['datum']) + '\n'

                    # # Open, write and close parameters file
                    oFile_PARAMS = open(join(sFolder_TMP, sFileName_TMP_RES_PARAMS), 'w')
                    oFile_PARAMS.writelines(oFileLines.values())
                    oFile_PARAMS.close()
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Command line resampling
                    sLineCmd_RES = (join(oDataSettings['mrt_info']['bin'], 'resample') + ' -p ' +
                                    join(sFolder_TMP, sFileName_TMP_RES_PARAMS))

                    # Execute mosaicking algorithm
                    oProcExec = Popen(sLineCmd_RES, shell=True,
                                      stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
                    oProcExec.communicate()
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Rename OUTCOME file
                    rename(join(sFolder_TMP, sFileName_TMP_RES_DATA), join(sFolder_OUTCOME, sFileName_OUTCOME_DATA))
                    # Info resampling
                    print(' =====> RESAMPLING DATA ... DONE!')
                    # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Condition about resampling not activated
                    rename(join(sFolder_TMP, sFileName_TMP_RES_DATA), join(sFolder_OUTCOME, sFileName_OUTCOME_DATA))
                    # Info resampling
                    print(' =====> RESAMPLING DATA ... NOT ACTIVATED!')
                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Condition about availability of expected outcome filename
                print(' ====> GET FILE: ' + sFileName_OUTCOME_DATA + ' ... DONE!')
                # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Condition about availability of expected outcome filename
                print(' ====> GET FILE: ' + sFileName_OUTCOME_DATA + ' ... FAILED. Tile(s) are not available!')
                # -------------------------------------------------------------------------------------
        else:
            # -------------------------------------------------------------------------------------
            # Condition about availability of expected outcome filename
            print(' ====> GET FILE: ' + sFileName_OUTCOME_DATA + ' ... SKIPPED. Data previously downloaded!')
            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Zip outcome filename (to save disk space)
        print(' ====> ZIP FILE: ' + sFileName_OUTCOME_DATA + ' ... ')
        if oDataSettings['data_info']['outcome']['zip'] is True:
            zipFile(join(sFolder_OUTCOME, sFileName_OUTCOME_DATA), join(sFolder_OUTCOME, sFileName_OUTCOME_ZIP))
            deleteFile(join(sFolder_OUTCOME, sFileName_OUTCOME_DATA))
            print(' ====> ZIP FILE: ' + sFileName_OUTCOME_DATA + ' ... DONE!')
        else:
            print(' ====> ZIP FILE: ' + sFileName_OUTCOME_DATA + ' ... SKIPPED! Zip file not activated!')

        # Delete all temporary files and script
        deleteFolder(sFolder_TMP)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    dTimeElapsed = round(time.time() - dStartTime, 1)

    print(' ')
    print(' ==> ' + sAlgName + ' (Version: ' + sAlgVersion + ' Release_Date: ' + sAlgRelease + ')')
    print(' ==> TIME ELAPSED: ' + str(dTimeElapsed) + ' seconds')
    print(' ==> ... END')
    print(' ==> Bye, Bye')
    print(' ============================================================================ ')
    # -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def getSettings():
    oParser = ArgumentParser()
    oParser.add_argument('-settingfile', action="store", dest="sFileSettings")
    oParserValue = oParser.parse_args()

    if oParserValue.sFileSettings:
        sFileSettings = oParserValue.sFileSettings
    else:
        sFileSettings = 'fp_downloader_modis_snow.json'

    return sFileSettings
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to gzip existing file
def zipFile(sFileName_UNCOMPRESSED, sFileName_COMPRESSED):
    if isfile(sFileName_UNCOMPRESSED):
        if not isfile(sFileName_COMPRESSED):
            if sFileName_UNCOMPRESSED != sFileName_COMPRESSED:
                with open(sFileName_UNCOMPRESSED, 'rb') as oFile_IN:
                    with gzip.open(sFileName_COMPRESSED, 'wb') as oFile_OUT:
                        copyfileobj(oFile_IN, oFile_OUT)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to remove file
def deleteFile(sFileName):
    if isfile(sFileName):
        remove(sFileName)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to delete folder and its content
def deleteFolder(sPathFolder):
    if exists(sPathFolder):
        rmtree(sPathFolder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def makeFolder(sPathFolder):
    if not exists(sPathFolder):
        makedirs(sPathFolder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make executable a bash file
def makeExec(path):
    mode = stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    chmod(path, mode)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set tag(s) in generic string
def setTags(sString, oTags):
    for sTagKey, sTagValue in oTags.items():
        sString = sString.replace(sTagKey, sTagValue)
    return sString
# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
