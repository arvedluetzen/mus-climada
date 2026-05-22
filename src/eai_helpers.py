from copy import deepcopy
import numpy as np
import pandas as pd
from climada.engine import ImpactCalc
from climada.entity import Exposures

def comp_impact(haz_dict, exposure_pnt_gdf):
    
    ## Poly -> Eigen Raster Exposure
    exposure_pnt_eigen_gdf = deepcopy(exposure_pnt_gdf)
    exposure_pnt_eigen_gdf["value"] = 1
    exposure_pnt_eigen = Exposures(exposure_pnt_eigen_gdf)
    
    ## Compute EAI per Hazard
    haz_eai = {}
    
    for haz_type, hazard in haz_dict.items():
        
        print(f"Computing {haz_type}")

        impact_pnt = ImpactCalc(
                exposure_pnt_eigen,
                impfset=hazard["impf_set"],
                hazard=hazard["hazard"]
            ).impact(save_mat=True)
        
        print(f"{np.mean(impact_pnt.eai_exp) = }")
        
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