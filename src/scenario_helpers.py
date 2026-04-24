import geopandas as gpd
import numpy as np
from copy import deepcopy


from src.helpers import comp_insurance
from src.helpers import comp_who_pays
from src.helpers import agg_to_departement

def comp_scenarios(
    exposure_pnt_gdf: gpd.GeoDataFrame,
    insurance_method: str = "coverage",
    insurance_scaling_factors: np.array = np.linspace(0, 1, 11) # Standard
) -> dict:
    
    final_results = {}
    
    for scaling_factor in insurance_scaling_factors:
        
        scenario_pnt = deepcopy(exposure_pnt_gdf)
        
        scenario_pnt["insurance"] = comp_insurance(
            method=insurance_method,
            scaling_factor=scaling_factor,
            insurance_current=scenario_pnt["insurance"],
            eai=scenario_pnt["eai"]
        )
        
        result = comp_who_pays(
            relative_damage=scenario_pnt["eai"],
            insured=scenario_pnt["insurance"]
        )

        scenario_pnt[["F", "I", "G"]] = result[["F", "I", "G"]].to_numpy()
        
        result = (scenario_pnt[['F', 'I', 'G']]
                .mul(scenario_pnt['eai'], axis=0)
                .mul(scenario_pnt["value"], axis=0)
                )

        scenario_pnt = scenario_pnt.join(result.add_suffix('_relative'))
        
        scenario_poly = agg_to_departement(
            pnt_gdf=scenario_pnt,
            value_cols=["value", "insurance", "eai", "F", "I", "G", "F_relative", "I_relative", "G_relative"],
            agg_func="mean"
        )
        
        result = scenario_poly[['F_relative', 'I_relative', 'G_relative']].mul(
            scenario_poly['area'], axis=0
        )

        result.columns = ['F_area', 'I_area', 'G_area']

        scenario_poly = scenario_poly.join(result)
        
        insured_area = (scenario_poly["insurance"] * scenario_poly["area"]).sum()
        
        who_pays_what = {
            "F": scenario_poly["F_area"].sum(),
            "I": scenario_poly["I_area"].sum(),
            "G": scenario_poly["G_area"].sum()
        }
        
        final_results[scaling_factor] = {
                "scenario_pnt": deepcopy(scenario_pnt),
                "scenario_poly": deepcopy(scenario_poly),
                "who_pays_what": deepcopy(who_pays_what),
                "insured_area": deepcopy(insured_area)
        }
        
    return final_results