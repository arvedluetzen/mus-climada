"""yearset_helpers.py
Contains all helper functions for the dataanalysis approach using yearsets.

Some functions are similar / the same from the EAI approach. To make the
codebase easier to read we decided to split the functionality fully.
Dataloading is still shared by both (see data_hazard.py and data_exposure.py)
"""

import numpy as np

def comp_who_pays_dense(
    damage,
    insurance_loc

):
    """Computes cost split for dense damage matrices.
    Uses France's insurance threshold scheme.

    Args:
        damage (NDArray): COO representation of yimp.imp_mat
        insurance_loc (np_1darray): Insurance level at all points with damage

    Returns:
        F, I, G: Vector for each actor with lenght of damage
    """
    
    ## Setting Conditions via standardized scheme
    cond_high = damage >= 0.5
    cond_mid  = (damage >= 0.2) & (damage < 0.5)
    cond_low  = damage < 0.2

    F = np.zeros_like(damage)
    I = np.zeros_like(damage)
    G = np.zeros_like(damage)

    # Farmer
    F = (
        cond_high * ((1 - insurance_loc) * 0.65) +
        cond_mid  * ((1 - insurance_loc) * 1.0) +
        cond_low  * 1.0
    )

    # Insurance
    I = (
        cond_high * (insurance_loc * 0.1) +
        cond_mid  * (insurance_loc * 1.0)
    )

    # Government
    G = (
        cond_high * (insurance_loc * 0.9 + (1 - insurance_loc) * 0.35)
    )
    
    return F, I, G

