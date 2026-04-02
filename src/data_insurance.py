from copy import deepcopy

def get_insurance(insurance_level: float, map_template):
    """_summary_

    Args:
        insurance_level (float): Value 0-1 of national insurance level
        map_template (Climada Polygon): exposure object

    Returns:
        GDF: with values for all departements
    """
    
    ## Make sure not to change the template
    insurance_gdf = deepcopy(map_template.gdf)

    ## Drop all impf Columns
    insurance_gdf = insurance_gdf.drop(columns=insurance_gdf.filter(regex="^impf_").columns)

    ## Set all Values Equal
    insurance_gdf["value"] = insurance_level
    
    return insurance_gdf