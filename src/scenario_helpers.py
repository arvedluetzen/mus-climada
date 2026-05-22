"""scenario_helpers.py
Functions for scenario computations (for both EAI and yearset approach)
- comp_insurance: Computes insurance scenarios
- Plotting functions for scenarios (absolute and difference)
"""

import geopandas as gpd
import numpy as np
from copy import deepcopy
import matplotlib.pyplot as plt
import matplotlib as mpl
import geopandas as gpd

from src.scenario_helpers import comp_insurance
from src.eai_helpers import comp_who_pays
from src.helpers import agg_to_departement


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


#############################################################
## PLOTTING HELPERS

def plot_scenario(scenario, title_addition=None):
    """
    Combined visualization:
    - Left: insured area
    - Right: 3 panels (farmer, insurance, government shares)
    """
    
    results = scenario["scenario_poly"]
    rel_max = scenario["relative_max"]

    cols = ["F_relative", "I_relative", "G_relative"]
    titles = ["Farmer", "Insurance", "Government"]

    # Create figure: 1 row, 4 columns
    fig, axes = plt.subplots(
        nrows=1,
        ncols=4,
        figsize=(22, 6),
        constrained_layout=True
    )

    # -------------------------------
    # 1) INSURANCE MAP (left panel)
    # -------------------------------
    results.plot(
        column="insurance",
        ax=axes[0],
        cmap="viridis",
        legend=True,
        edgecolor="black",
        linewidth=0.5,
        vmin=0,
        vmax=1
    )
    axes[0].set_title("Insurance Coverage [%]")
    axes[0].set_axis_off()

    # -------------------------------
    # 2) SHARED NORMALIZATION (right 3 panels)
    # -------------------------------
    vmin = 0
    vmax = rel_max
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    cmap = "viridis"

    # -------------------------------
    # 3) PLOT RELATIVE CONTRIBUTIONS
    # -------------------------------
    for ax, col, title in zip(axes[1:], cols, titles):
        results.plot(
            column=col,
            ax=ax,
            cmap=cmap,
            norm=norm,
            edgecolor="black",
            linewidth=0.4
        )
        ax.set_title(title)
        ax.set_axis_off()

    # -------------------------------
    # 4) SINGLE COLORBAR FOR SHARES
    # -------------------------------
    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    cbar = fig.colorbar(
        sm,
        ax=axes[1:],   # only attach to the 3 right plots
        orientation="vertical",
        fraction=0.025,
        pad=0.02
    )
    cbar.set_label("Relative Area [%EAI × %Farm Land]")
    
    title = "Insurance Coverage and Cost Distribution by Department"
    if title_addition:
        title = title + " " + title_addition
    fig.suptitle(title, fontsize=16, fontweight="bold")

    return fig, axes



def plot_difference(baseline_scenario, compare_scenario,
                    rel_max=None, title_addition=None):

    base = baseline_scenario["scenario_poly"].copy()
    comp = compare_scenario["scenario_poly"].copy()

    diff = base.copy()

    cols = ["F_relative", "I_relative", "G_relative"]
    for col in cols:
        diff[col] = comp[col] - base[col]

    # -----------------------------------
    # SEPARATE NORMALIZATION
    # -----------------------------------

    # Insurance scale (own scale)
    norm_ins = mpl.colors.Normalize(
        vmin=0,
        vmax=1
    )
    cmap_ins = "viridis"

    # Relative panels scale (shared)
    rel_cols = ["F_relative", "I_relative", "G_relative"]

    if rel_max is None:
        
        rel_max = max(abs(diff[col]).max() for col in rel_cols)

    norm_rel = mpl.colors.TwoSlopeNorm(
        vmin=-rel_max,
        vcenter=0,
        vmax=rel_max
    )

    cmap_rel = "RdBu_r"

    # -----------------------------------
    # FIGURE
    # -----------------------------------
    fig, axes = plt.subplots(
        nrows=1,
        ncols=4,
        figsize=(22, 6),
        constrained_layout=True
    )

    titles = [
        "Insurance Coverage [%]",
        "Farmer",
        "Insurance",
        "Government"
    ]

    # -----------------------------------
    # PLOT PANELS
    # -----------------------------------

    # FIRST PANEL (different scale + cmap)
    comp.plot(
        column="insurance",
        ax=axes[0],
        cmap=cmap_ins,
        norm=norm_ins,
        edgecolor="black",
        linewidth=0.4
    )

    axes[0].set_title(titles[0])
    axes[0].set_axis_off()

    # REMAINING THREE (shared scale)
    for ax, col, title in zip(axes[1:], rel_cols, titles[1:]):

        diff.plot(
            column=col,
            ax=ax,
            cmap=cmap_rel,
            norm=norm_rel,
            edgecolor="black",
            linewidth=0.4
        )

        ax.set_title(title)
        ax.set_axis_off()

    # -----------------------------------
    # COLORBARS
    # -----------------------------------

    # Insurance colorbar
    sm1 = mpl.cm.ScalarMappable(cmap=cmap_ins, norm=norm_ins)
    sm1.set_array([])

    cbar1 = fig.colorbar(
        sm1,
        ax=axes[0],
        orientation="vertical",
        fraction=0.04,
        pad=0.02
    )
    # cbar1.set_label("Insurance difference")

    # Shared colorbar (right 3 panels)
    sm2 = mpl.cm.ScalarMappable(cmap=cmap_rel, norm=norm_rel)
    sm2.set_array([])

    cbar2 = fig.colorbar(
        sm2,
        ax=axes[1:],
        orientation="vertical",
        fraction=0.025,
        pad=0.02
    )
    cbar2.set_label("Difference in Relative Area [%EAI × %Farm Land]")

    # -----------------------------------
    # TITLE
    # -----------------------------------
    title = "Insurance Coverage Scenario and Differences in Cost Distribution"
    if title_addition:
        title = title + " " + title_addition
    
    fig.suptitle(
        title,
        fontsize=16,
        fontweight="bold"
    )

    return fig, axes