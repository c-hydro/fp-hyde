# -------------------------------------------------------------------------------------
# Library
import numpy as np

from pygeobase.object_base import Image

byte_nan = np.iinfo(np.byte).min
ubyte_nan = np.iinfo(np.ubyte).max
uint8_nan = np.iinfo(np.uint8).max
uint16_nan = np.iinfo(np.uint16).max
uint32_nan = np.iinfo(np.uint32).max
float32_nan = np.finfo(np.float32).min
float64_nan = np.finfo(np.float64).min
long_nan = np.iinfo(np.int32).min
int_nan = np.iinfo(np.int16).min
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Library
# Method to mask data using flag(s)
def read_masked_data(orbit, correction_flag=0, processing_flag=0,
                     aggregated_quality_flag=100,
                     snow_cover_probability=100,
                     frozen_soil_probability=100,
                     inudation_or_wetland=100,
                     topographical_complexity=100):
    """
    Read ASCAT swath files and mask unusable observations.

    Parameters
    ----------
    correction_flag : int, optional
        Correction flag (default: 0).
    aggregated_quality_flag : int, optional
        Aggregated quality flag (default: 0).
    snow_cover_probability : float, optional
        Snow cover probability (default: 100).
    frozen_soil_probability : float, optional
        Frozen soil probability (default: 100).
    innudation_or_wetland : float, optional
        Innundation and wetland flag (default: 100).
    topographical_complexity, float, optional
        Toographical complexity flag (default: 100).

    Returns
    -------
    img : pygeobase.object_base.Image
        ASCAT swath image with masking applied.
    """

    n = orbit.data[list(orbit.data.keys())[0]].shape[0]

    valid = np.ones(n, dtype=np.bool)

    # bitwise comparison, if any bitflag is set by the user and is active
    # for the datarecord the result is bigger than 0 and the not valid
    valid = (valid & (((orbit.data['Soil Moisture Correction Flag'] == 0) & (correction_flag == 0))
                      | (orbit.data['Soil Moisture Correction Flag'] == uint8_nan)))

    valid = (valid & (((orbit.data['Soil Moisture Processing Flag'] == 0) & (processing_flag == 0))
                      | (orbit.data['Soil Moisture Processing Flag'] == uint16_nan)))

    # if any probability/flag is too high the datarecord is not used
    # nan values are not considered since not all formats provide all flags
    # and the values are set to nan there to keep a generic structure
    valid = (valid & ((orbit.data['Soil Moisture Quality']
                       < aggregated_quality_flag)
                      | (orbit.data['Soil Moisture Quality']
                         == uint8_nan)))

    valid = (valid & ((orbit.data['Snow Cover']
                       < snow_cover_probability)
                      | (orbit.data['Snow Cover']
                         == float32_nan)))

    valid = (valid & ((orbit.data['Frozen Land Surface Fraction']
                       < frozen_soil_probability)
                      | (orbit.data['Frozen Land Surface Fraction']
                         == float32_nan)))

    valid = (valid & ((orbit.data['Inundation And Wetland Fraction']
                       < inudation_or_wetland) |
                      (orbit.data['Inundation And Wetland Fraction']
                       == float32_nan)))

    valid = (valid & ((orbit.data['Topographic Complexity']
                       < topographical_complexity)
                      | (orbit.data['Topographic Complexity']
                         == float32_nan)))

    valid_num = orbit.data['jd'][valid].shape[0]

    masked_data = {}
    for key in list(orbit.data.keys()):
        masked_data[key] = orbit.data[key][valid]

    img = Image(orbit.lon[valid], orbit.lat[valid], masked_data,
                orbit.metadata, orbit.timestamp, timekey='jd')

    return img
# -------------------------------------------------------------------------------------
