"""helpers.py
Functions that are 
"""

import geopandas as gpd

def agg_to_departement(
    pnt_gdf: gpd.GeoDataFrame,
    value_cols: list,
    poly_col: str = "geometry_orig",
    dep_cols: list = ["DDEP_C_COD", "DDEP_L_LIB", "DREG_L_LIB", "area"],
    agg_func: str | dict = "mean"
):
    """
    Reaggregate point-level data to original department polygons.

    value_cols: columns to aggregate (e.g. value, insurance)
    agg_func: 'sum', 'mean', or dict like {'insurance': 'sum', 'eai': 'mean'}
    """

    # Build aggregation dictionary
    agg_dict = {col: agg_func for col in value_cols}

    # Ensure geometry is preserved (take first polygon per group)
    agg_dict[poly_col] = "first"

    # Group and aggregate
    dep_gdf = (
        pnt_gdf
        .groupby(dep_cols, as_index=False)
        .agg(agg_dict)
        .set_geometry(poly_col)
        .set_crs(pnt_gdf.crs)
    )

    return dep_gdf