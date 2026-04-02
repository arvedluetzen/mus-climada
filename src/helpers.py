from copy import deepcopy
import numpy as np
from climada.entity import Exposures
import climada.util.lines_polys_handler as u_lp

def comp_impact(haz_dict, exposure_template):
    """Function that Calculates the Cummulative EAI over multiple Hazard Types

    Args:
        haz_dict (_type_): Dictionary with Hazards and their impact functions
        exposure_template (_type_): A template of how the Exposure Set will look like

    Returns:
        GDF: Exposure as GDF with a new Column the Commulative EAI
    """
    
    ## Create an Exposure Map with only 1s
    exposure_eigen_gdf = deepcopy(exposure_template.gdf)
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
    
    exposure = deepcopy(exposure_template.gdf)

    exposure["commulative_eai"] = commulative_eai
    
    return exposure