from copy import deepcopy
import numpy as np
import pandas as pd
from climada.entity import Exposures
import climada.util.lines_polys_handler as u_lp

def comp_impact(haz_dict, exposure):
    """Function that Calculates the Cummulative EAI over multiple Hazard Types

    Args:
        haz_dict (_type_): Dictionary with Hazards and their impact functions
        exposure_template (_type_): A template of how the Exposure Set will look like

    Returns:
        Array: Of Commulative EAI
    """
    
    ## Create an Exposure Map with only 1s
    exposure_eigen_gdf = deepcopy(exposure.gdf)
    exposure_eigen_gdf["value"] = 1
    exposure_eigen_poly = Exposures(exposure_eigen_gdf)
    
    ## Compute the EAI for each Hazard x Impact Function
    haz_eai = {}
    for haz_type, hazard in haz_dict.items():
        
        ## Automatic Computation using Polygons:
        # Dissagg: Splits the Exposure Value into Number of Pixels
        # Agg: Sums up all Damages
        # -> Same effect as not splitting Exposure and then taking a mean
        # SUM((exposure / N) * Impactvalue) = SUM (Exposure * Impactvalue) / N 
        
        impact = u_lp.calc_geom_impact(
            exp=exposure_eigen_poly,
            impf_set=hazard["impf_set"],
            haz=hazard["hazard"],
            res=0.05,
            to_meters=False,
            disagg_met=u_lp.DisaggMethod.DIV,
            disagg_val=None,
            agg_met=u_lp.AggMethod.SUM,
        )
        
        ## Clipping EAI at 1
        ## Make sure Hazard x Impactfunction make sense (not too many >1)
        eai_exp = np.clip(impact.eai_exp, a_min=0, a_max=1)
        haz_eai[haz_type] = eai_exp

    ## Aggregating multiple Hazards together:
    ## (1 - eai_WS) * (1 - eai_FL) * ...
    remaining_value = np.ones_like(eai_exp)
    for haz_type, eai in haz_eai.items():
        remaining_value *= (1 - eai)
    
    ## Going from Relative Remaining Value to EAI
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
        