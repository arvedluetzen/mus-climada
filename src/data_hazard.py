import numpy as np
import xarray as xr
from pathlib import Path
from scipy import sparse
from climada.hazard import Hazard
from climada.hazard.centroids import Centroids
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
        get_TC(),
        get_TP(),
        get_HL(),
        get_FL()
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
    
    impf_WS_test = ImpactFunc(
        id=1,
        name = "Storm Impact Function",
        intensity_unit="m/s",
        haz_type=hazard.haz_type,
        intensity=np.array([0, 12.1, 14.8, 16.8, 22, 100]),
        mdd=np.array([0.0, 0.1, 0.2, 0.4, 0.5, 1.0]),
        paa = np.ones(6)
    )
    
    impf_WS_set = ImpactFuncSet([impf_WS_test])
    
    return {
        "haz_type": hazard.haz_type, # Replace with Climada readable abbreviation
        "hazard": hazard, # Climada Hazard Object
        "impf_set": impf_WS_set # Impf already as set (to make later computations easier)
    }
    
    
def get_TC ():
    
    SRC_DIR = Path.cwd()
    PROJECT_ROOT = SRC_DIR.parent
    DATA_DIR = PROJECT_ROOT / "data" / "2m_temperature"
    
    ## Load Hazard from NetCDF Files

    ds = xr.open_mfdataset(
        str(DATA_DIR / "*.nc"),
        combine="by_coords"
    )

    ## Converting Xarray to CLIMADA Hazard
    
    #Creating Centriods for Data
    lats = ds.latitude.values
    lons = ds.longitude.values
    # Build 2D grid
    lon2d, lat2d = np.meshgrid(lons, lats)
    centroids = Centroids(
        lat=lat2d.ravel(),
        lon=lon2d.ravel()
    )
    
    # (valid_time, latitude, longitude)
    t2m = ds["t2m"].values
    # Convert Kelvin → Celsius (important for impact functions)
    t2m = t2m - 273.15
    
    n_events = t2m.shape[0]
    n_centroids = t2m.shape[1] * t2m.shape[2]
    
    ## Creating Hazard
    hazard = Hazard(haz_type="TC")

    # --- REQUIRED: centroids ---
    hazard.centroids = centroids   # <-- you MUST set this

    # --- Dense first ---
    intensity_dense = t2m.reshape(n_events, n_centroids)
    fraction_dense  = np.ones_like(intensity_dense)

    # --- Convert once to sparse ---
    hazard.intensity = sparse.csr_matrix(intensity_dense)
    hazard.fraction  = sparse.csr_matrix(fraction_dense)

    # --- Events ---
    hazard.event_id = np.arange(1, n_events + 1)
    hazard.event_name = np.array([f"event_{i}" for i in hazard.event_id])
    hazard.date = ds.valid_time.dt.date.values.astype("datetime64[D]")

    # April–Sept only: but frequency must sum to 1
    hazard.frequency = np.ones(n_events) / 365

    # --- Metadata ---
    hazard.units = "degC"
    hazard.tag = {
        "source": "ECMWF ERA",
        "description": "Daily mean 2m temperature, April–September 1990-2000"
    }
    
    ## Define Respective Impact Function
    
    # Parabel
    #temps = np.linspace(-10, 40, 100)
    # a = 0.05 / (18**2)
    # damage = a * (temps - 12)**2
    # damage = np.clip(damage, 0, 1)
    
    # Logistic
    # temps = np.linspace(-10, 45, 200)
    # T0 = 30     # inflection point
    # k = 0.3     # steepness
    # scale = 0.01  # daily impact scaling

    # damage = scale * (1 / (1 + np.exp(-k * (temps - T0))))
    # damage = np.clip(damage, 0, 1)
    
    # Threshold:
    # < 32 Degrees = 0 % Damage
    # 32 Degrees = 1 % Damage
    # Every Degree above that + 0.05 Degrees

    temps = np.linspace(-10, 45, 200)

    threshold = 28.0        # 32 for Daily Max Temperature
    base_damage = 0.01      # 1% at threshold
    slope = 0.005           # +0.5% per °C above threshold

    damage = np.where(
        temps <= threshold,
        0.0,
        base_damage + slope * (temps - threshold)
    )
    
    impf_TC = ImpactFunc(
        id=1,
        name = "Parabolic temp damage Impact Function",
        intensity_unit="m/s",
        haz_type=hazard.haz_type,
        intensity=temps,
        mdd=damage,
        paa = np.ones_like(temps)
    )
    
    impf_TC_set = ImpactFuncSet([impf_TC])
    
    return {
        "haz_type": hazard.haz_type, # Replace with Climada readable abbreviation
        "hazard": hazard, # Climada Hazard Object
        "impf_set": impf_TC_set # Impf already as set (to make later computations easier)
    }
    
    
def get_TP ():
    
    SRC_DIR = Path.cwd()
    PROJECT_ROOT = SRC_DIR.parent
    DATA_DIR = PROJECT_ROOT / "data" / "total_precipitation"
    
    ## Load Hazard from NetCDF Files

    ds = xr.open_mfdataset(
        str(DATA_DIR / "*.nc"),
        combine="by_coords"
    )

    ## Converting Xarray to CLIMADA Hazard
    
    #Creating Centriods for Data
    lats = ds.latitude.values
    lons = ds.longitude.values
    # Build 2D grid
    lon2d, lat2d = np.meshgrid(lons, lats)
    centroids = Centroids(
        lat=lat2d.ravel(),
        lon=lon2d.ravel()
    )
    
    # (valid_time, latitude, longitude)
    tp = ds["tp"].values
    tp = tp * 1000 # Change to mm
    
    n_events = tp.shape[0]
    n_centroids = tp.shape[1] * tp.shape[2]
    
    ## Creating Hazard
    hazard = Hazard(haz_type="TP")

    # --- REQUIRED: centroids ---
    hazard.centroids = centroids   # <-- you MUST set this

    # --- Dense first ---
    intensity_dense = tp.reshape(n_events, n_centroids)
    fraction_dense  = np.ones_like(intensity_dense)

    # --- Convert once to sparse ---
    hazard.intensity = sparse.csr_matrix(intensity_dense)
    hazard.fraction  = sparse.csr_matrix(fraction_dense)

    # --- Events ---
    hazard.event_id = np.arange(1, n_events + 1)
    hazard.event_name = np.array([f"event_{i}" for i in hazard.event_id])
    hazard.date = ds.valid_time.dt.date.values.astype("datetime64[D]")

    # April–Sept only: but frequency must sum to 1
    hazard.frequency = np.ones(n_events) / 365

    # --- Metadata ---
    hazard.units = "mm"
    hazard.tag = {
        "source": "ECMWF ERA",
        "description": "Daily total precipitation, April–September 1990-2000"
    }
    
    ## Define Respective Impact Function
    precipitation = np.array([0, 20, 40, 60, 80, 120])
    damage = np.array([0, 0, 0.05, 0.2, 0.5, 0.9])
    
    impf_TP = ImpactFunc(
        id=1,
        name = "Total Precipitation ChatGPT Function",
        intensity_unit="mm",
        haz_type=hazard.haz_type,
        intensity=precipitation,
        mdd=damage,
        paa = np.ones_like(precipitation)
    )
    
    impf_TP_set = ImpactFuncSet([impf_TP])
    
    return {
        "haz_type": hazard.haz_type, # Replace with Climada readable abbreviation
        "hazard": hazard, # Climada Hazard Object
        "impf_set": impf_TP_set # Impf already as set (to make later computations easier)
    }
    
def get_HL ():
    
    ## Get Hazard
    client = Client()
    ISO = "FRA"
    hazard = client.get_hazard(
        "hail",
        properties={
            "country_iso3alpha": ISO,
            'climate_scenario': 'REF'}
        )
    
    ## Define Respective Impact Function
    diameter = np.array([0, 6, 10, 20, 30, 50])

    # Mean Damage Degree (0–1)
    damage = np.array([0.0, 0.05, 0.15, 0.35, 0.60, 0.90])
    
    impf_HL = ImpactFunc(
        id=1,
        name = "Hail Impact Function",
        intensity_unit="mm",
        haz_type=hazard.haz_type,
        intensity=diameter,
        mdd=damage,
        paa = np.ones_like(diameter)
    )
    
    impf_HL_set = ImpactFuncSet([impf_HL])
    
    return {
        "haz_type": hazard.haz_type, # Replace with Climada readable abbreviation
        "hazard": hazard, # Climada Hazard Object
        "impf_set": impf_HL_set # Impf already as set (to make later computations easier)
    }
    
def get_FL ():
    
    ## Get Hazard
    client = Client()
    ISO = "FRA"
    hazard = client.get_hazard("flood", properties={
        'res_meter': ['250'],
        'spatial_coverage': ['country'],
        'year_range': ['2002_2019'],
        'country_iso3alpha': ISO,
        'country_name': ['France']
        })
    
    ## Define Respective Impact Function
    intensity = np.array([0., 0.05, 0.5, 1., 1.5, 2., 3., 4., 5., 6., 12.])
    damage = np.array([0., 0., 0.3, 0.55,  0.65, 0.75,  0.85, 0.95, 1., 1., 1.])

    impf_FL = ImpactFunc(
        id=1,
        name = "Hail Impact Function",
        intensity_unit="mm",
        haz_type=hazard.haz_type,
        intensity=intensity,
        mdd=damage,
        paa = np.ones_like(intensity)
    )
    
    impf_FL_set = ImpactFuncSet([impf_FL])
    
    return {
        "haz_type": hazard.haz_type, # Replace with Climada readable abbreviation
        "hazard": hazard, # Climada Hazard Object
        "impf_set": impf_FL_set # Impf already as set (to make later computations easier)
    }