import numpy as np
from climada.util.api_client import Client
from climada.entity import ImpactFunc
from climada.entity.impact_funcs import ImpactFuncSet

## Main Functions for use in other Notebooks
def get_haz_dict():
    """
    Function that uses different Hazard Functions
    to create a dictionary of hazards with:
    keys = haz_type
    values = dictionary with hazard and impact function
    """
    ## Add new get_hazard Functions as they come
    hazards = [
        get_WS()
    ]
    
    haz_dict = {}
    
    for hazard in hazards:
        haz_dict[hazard["haz_type"]] = {
            "hazard": hazard["hazard"],
            "impf_set": hazard["impf_set"]
        }
    
    return haz_dict

#########################################
## Functions for Specific Hazards and their Impact Functions
## Make sure to add them into the get_haz_dict() function

def get_WS ():
    
    ## Get Hazard
    client = Client()
    ISO = "FRA"
    hazard = client.get_hazard(
        "storm_europe",
        properties={"country_iso3alpha": ISO}
    )
    
    ## Define Respective Impact Function
    impf_WS = ImpactFunc(
        id=1,
        name = "Storm Impact Function",
        intensity_unit="m/s",
        haz_type=hazard.haz_type,
        intensity=np.array([0, 12.1, 14.8, 16.8, 22]),
        mdd=np.array([0.0, 0.2, 0.4, 0.8, 1.0]),
        paa = np.ones(5)
    )
    
    impf_WS_set = ImpactFuncSet([impf_WS])
    
    return {
        "haz_type": hazard.haz_type, # Replace with Climada readable abbreviation
        "hazard": hazard, # Climada Hazard Object
        "impf_set": impf_WS_set # Impf already as set (to make later computations easier)
    }