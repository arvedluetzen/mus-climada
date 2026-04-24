from copy import deepcopy
import numpy as np
import pandas as pd
import geopandas as gpd
from climada.engine import ImpactCalc
from climada.entity import Exposures
import climada.util.lines_polys_handler as u_lp

def comp_impact(haz_dict, exposure_pnt_gdf):
    
    ## Poly -> Eigen Raster Exposure
    exposure_pnt_eigen_gdf = deepcopy(exposure_pnt_gdf)
    exposure_pnt_eigen_gdf["value"] = 1
    exposure_pnt_eigen = Exposures(exposure_pnt_eigen_gdf)
    
    ## Compute EAI per Hazard
    haz_eai = {}
    
    for haz_type, hazard in haz_dict.items():

        impact_pnt = ImpactCalc(
                exposure_pnt_eigen,
                impfset=hazard["impf_set"],
                hazard=hazard["hazard"]
            ).impact(save_mat=True)

        eai = np.clip(impact_pnt.eai_exp, a_min=0, a_max=1)
        haz_eai[haz_type] = eai
    
    ## Aggregate Hazards at each Pixel
    remaining_value = np.ones_like(eai)
    for haz_type, eai in haz_eai.items():
        remaining_value *= (1 - eai)
    
    commulative_eai = 1 - remaining_value
    
    return commulative_eai


def comp_damage_map (eai, value, area):
    """Combines:
    Area per Departement
    Commulative EAI over different Hazards
    Relative Agriculture Area
    
    Into:
    Expected Annual Damaged Area
    """
    
    rel_damaged = eai * value
    damaged_area = area * rel_damaged
    
    return damaged_area


def comp_who_pays(relative_damage, insured):
    """Computes which actors pay which part of the damage

    Args:
        relative_damage (array): eai in departement
        insured (array): percentage of insured people in location

    Returns:
        pd.DataFrame: 3 Cols for F, I , G
    """

    condlist = [
        relative_damage >= 0.5,
        (relative_damage >= 0.2) & (relative_damage < 0.5),
        relative_damage < 0.2
    ]

    # Payments for conditions in order: F, I, G
    F = np.select(condlist, [
            insured * 0 + (1 - insured) * 0.65,
            insured * 0 + (1 - insured) * 1,
            1
        ])

    I = np.select(condlist, [
            insured * 0.1 + (1 - insured) * 0,
            insured * 1   + (1 - insured) * 0,
            0
        ])

    G = np.select(condlist, [
            insured * 0.9 + (1 - insured) * 0.35,
            0,
            0
        ])

    return pd.DataFrame({"F": F, "I": I, "G": G})


def comp_outcome (damaged_area, who_pays):

    ## Which Actor is responsible for how much area in each Departement
    result = who_pays.multiply(damaged_area, axis=0)

    ## Aggregate over all of France
    absolute = result.sum()
    relative = absolute / damaged_area.sum()
    
    return {
        "who_pays_area": result,
        "agg_absolute": absolute,
        "agg_relative": relative
    }
    

def comp_insurance (
    method: str,
    scaling_factor: float,
    insurance_current,
    eai = None
    ):
    
    """Computes Scenarios for Insurance Coverage Development
    
    scaling_factor: how much does it increase

    method:
    - "constant": increases by the same fraction
    - "coverage": increases by (1-current coverage) * scaling_factor
    - "eai": increases by 1/eai

    Returns:
        Vector with Insurance Coverage per Departement
    """
    
    assert (method in ["constant", "coverage", "eai"]), "Wrong Method Specified"
    
    if method == "eai":
        assert (eai is not None), "If method = eai, please Provide EAI Vector"
        
    assert (scaling_factor <=1 and scaling_factor>=0), "Scaling Factor must be between 0 and 1"
        
    if method == "constant":
        insurance_new = insurance_current + scaling_factor
        
    elif method == "coverage":
        insurance_new = insurance_current + (1 - insurance_current) * scaling_factor
        
    elif method == "eai":
        norm_factor = 1 / eai.max()
        eai = eai * norm_factor
        
        insurance_new = insurance_current + (eai * scaling_factor)
        
    else:  
        raise Exception("Wrong Method Input")
    
    insurance_new = insurance_new.clip(lower=0, upper=1)
    return insurance_new


def agg_to_departement(
    pnt_gdf: gpd.GeoDataFrame,
    value_cols: list,
    poly_col: str = "geometry_orig",
    dep_cols: list = ["DDEP_C_COD", "DDEP_L_LIB", "DREG_L_LIB", "area"],
    agg_func: str | dict = "mean"
):
    """
    Reaggregate point-level data to original department polygons.

    value_cols: columns to aggregate (e.g. value, insurance)
    agg_func: 'sum', 'mean', or dict like {'insurance': 'sum', 'eai': 'mean'}
    """

    # Build aggregation dictionary
    agg_dict = {col: agg_func for col in value_cols}

    # Ensure geometry is preserved (take first polygon per group)
    agg_dict[poly_col] = "first"

    # Group and aggregate
    dep_gdf = (
        pnt_gdf
        .groupby(dep_cols, as_index=False)
        .agg(agg_dict)
        .set_geometry(poly_col)
        .set_crs(pnt_gdf.crs)
    )

    return dep_gdf
        