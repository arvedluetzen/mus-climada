import geopandas as gpd
import numpy as np
from copy import deepcopy

import matplotlib.pyplot as plt
import matplotlib as mpl
import geopandas as gpd

from src.helpers import comp_insurance
from src.helpers import comp_who_pays
from src.helpers import agg_to_departement

def comp_scenarios(
    exposure_pnt_gdf: gpd.GeoDataFrame,
    insurance_method: str = "coverage",
    insurance_scaling_factors: np.array = np.linspace(0, 1, 11) # Standard
) -> dict:
    
    final_results = {}
    relative_max = 0
    
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
        
        relative_max = max(relative_max, scenario_poly[['F_relative', 'I_relative', 'G_relative']].max().max())

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
                "insured_area": deepcopy(insured_area),
        }
    
    for label, scenario in final_results.items():
        scenario["relative_max"] = relative_max   
        
    return final_results


################################################
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