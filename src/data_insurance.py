from copy import deepcopy

## Has to get adjusted when making it more detailed
## Either Return an Integer or length 96 for each departement 1 value
def get_insurance(insurance_level: float):
    """_summary_

    Args:
        insurance_level (float): Value 0-1 of national insurance level
        map_template (Climada Polygon): exposure object

    Returns:
        GDF: with values for all departements
    """
    
    return insurance_level