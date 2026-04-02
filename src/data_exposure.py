import json
import pandas as pd
import numpy as np
import geopandas as gpd
from climada.entity import Exposures
from shapely.geometry import shape
from src.config import DATA_PATH

def get_exposure(hazard_types: list):
    """Returns Exposure Data in Climada Readable Polygons

    Args:
        hazard_types (list): List of 2 Letter Acronyms of Hazards
        (for impf_WS column)

    Returns:
        climada.entity.exposures.base.Exposures: exposure map
    """

    ## Departement Boundaries
    # import departement boundaries
    boundaries_df = pd.read_csv(DATA_PATH + "geo-contours-departements.csv")
    boundaries_df = boundaries_df.dropna(subset=["geometry"])
    boundaries_df["geometry"] = boundaries_df["geometry"].apply(lambda x: shape(json.loads(x)))

    boundaries_gdf = gpd.GeoDataFrame(boundaries_df, geometry="geometry")

    ## Crop Data per Departement
    # import crop data per departement
    crop_df = pd.read_excel(DATA_PATH +"crop_data_france.xlsx")

    # Rename to obtain a key to merge
    crop_df = crop_df.rename(columns={"number_department": "DDEP_C_COD"})

    # Merge with Geometry + Data
    exposure_gdf = boundaries_gdf.merge(crop_df.iloc[:, [0, 2, 3]], on="DDEP_C_COD")

    ## Process Data for CLIMADA
    # Rename to obtain a key to merge
    exposure_gdf["value"] = exposure_gdf["value"].replace("s", np.nan) # remove lines with value = "S" --> secret statistique mdr
    exposure_gdf["value"] = exposure_gdf["value"] / 100
    
    # add impact function column in exposure data
    for hazard in hazard_types:
        exposure_gdf["impf_" + hazard] = 1

    # create Exposure object out of dataframe
    exposure_poly = Exposures(exposure_gdf) 
    
    return exposure_poly