import numpy as np
from climada.util.api_client import Client
from climada.entity import ImpactFunc
from climada.entity.impact_funcs import ImpactFuncSet

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