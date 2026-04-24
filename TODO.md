# ToDos Praktikum bis Hand in Policy Brief (22. Mai)

> 5 volle Tage Arbeit

Abgaben:
- Policy Brief
- Technischer Anhang
- CLIMADA Code

## Ablauf

**24. April**
- Policy Brief + Technischer Anhang Outline / Draft (Sarah-Rose + Marie)
- Quantitative: Fix Who Pays What + Clean Up (Arved)

**30. April**
- Präsentation (alle)

**7. Mai (max 1-2h Arbeitszeit)**

**8. Mai**

**21. Mai**

**22. Mai**

# Policy Brief




# ToDos for the Quantitative Part

- Event Frequency of Percipitation and Heat (/n years)
- Von Hand Cost Benefit analysis: take into account that costs are at one point and that benefits are in the long run (aka discounting)
- climate change scenarios (use the same for all hazards, interpolation to get value per year)
- How does France Wide Who Pays change with scaling factor


### Change when "who pays what" is computed to allow for local minima (per pixel and not per polygone)

https://climada-python.readthedocs.io/en/v6.1.0/user-guide/climada_entity_Exposures_polygons_lines.html

1. Disaggregate Manually
2. Impact Calc
3. Apply Who Pays What -> add three columns (aka 3 Maps) 

Function (comp_impact) Returns Dictionary with Raw and Aggregated. Each with 4 Maps: Raw Impact + Who Pays how much at each Pixel (3 Maps)

- Think about comp_outcome (if it still works)
- Resolution
- How to Put Hazards together

