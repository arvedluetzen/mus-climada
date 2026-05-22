# mus-climada

Quantitative Analysis for Group Work in FS2026 "Praktikum Mensch- und Umweltsysteme" at ETH Zürich

## Background

Unser Projekt im Rahmen des Praktikums fokussiert sich auf Ernteversicherungen in Frankreich. Obwohl diese als wichtige Massnahme angesehen werden, Landwirtschaft and den Klimawandel anzupassen, ist die Versicherungsabdeckung in Frankreich sehr niedrig. Wir wollten herausfinden wieso dies so ist, was gemacht werden kann, um das zu ändern, und welchen Einfluss das auf die Kostenverteilung zwischen den Akteuren hat. Für letzteres haben wir diese quantitative Analyse durchgeführt.

> Genauere Hintergründe und Resultate unseres Projekts sind im Policy Brief und technischem Anhang zu finden.

Eine "klassische" CLIMADA Analyse ergab mit unserem Thema von Versicherungen wenig Sinn. Die Versicherungsabdeckung zu verändern, hat weder einen Einfluss auf die Vulnerability noch auf Hazard oder Exposure (Auf jeden Fall nicht direkt). Die Frage, die wir zu beantworten versuchen ist wie sich die Kostenlast zwischen den Akteuren Bauern, Versicherungen und Staat verteilt, wenn sich die Versicherungsabdeckung ändert. Konzeptionell sollten davon sowohl Bauern als auch Versicherungen profitieren. Dies in einem Modell auszudrücken, erfordert folgende Informationen:

•	Hazard: Informationen über wetterbedingten Schaden an jedem Ort in Frankreich. In unserem Fall ist jedoch entscheidend, dass die staatlich subventionierte Versicherung 15 verschiedene Hazards abdeckt. Wir müssen also einen Weg finden mehrere zu kombinieren. Dies ist nicht in CLIMADA implementiert. Dies sinnvoll zu machen, ist der zentrale Teil unserer Analyse. Wir betrachten die Auswahl von Hitze, Niederschlag, Hagel und Flussüberschwemmungen.
•	Exposure: Um die Verteilung der Hazards mit Landwirtschaftsfläche zu kombinieren, brauchen wir gewisse Informationen, über wo in Frankreich Landwirtschaft betrieben wird. Um diesen Teil der Analyse einfach zu halten, haben wir uns hierbei auf Departementweite Zahlen beschränkt und betrachten nur die sogenannte «Grande culture» (Getreide, Ölsaaten und Eiweisspflanzen).

Basierend auf diesen Daten haben wir einen längeren, iterativen Prozess durchgelaufen. Mehrmals haben wir die Limitierungen unserer Ideen festgestellt und basierend darauf unseren Ansatz angepasst.

---

# Erklärung Ansatz

## Ansatz: Expected Annual Impact

> Siehe Notebook 0424_pipeline-scenarios.ipynb

Unser Ziel, den akkumulierten EAI zu berechnen, haben wir mit relativen Impacts gerechnet:

1. Mit CLIMADA's ImpactCalc den Impact für jeden Hazard einzeln ausrechnen. Hierbei haben wir einen "Eigen-Exposure" verwendet, bei welchem wir auf der Vorlage des "echten" Exposure Objekts, alle Werte auf 1 gesetzt haben. Dies führt dazu, dass der Output der ImpactCalc rein relativ ist und noch nicht auf eine Exposure skaliert.
2. Die relativen Impacts werden pro Pixel miteinander multipliziert: (1 - EAI_heat) x (1 - EAI_hail) x ... Unser Argument hierfür ist, dass Schäden nicht additiv sind, sondern auf das "zurückbleibende" wirken. Dies ist noch immer eine Starke annahme und vernachlässigt viele reale Interkationen zwischen Hazards (Man denke Beispielsweise wie eine Hitzewelle, die die Böden ausgetrocknet hat, Starkniederschläge verschlimmert, weil Böden weniger bereit sind Wasser aufzunehmen. Auch die Reihenfolge wird nicht in Betracht gezogen.)
3. Basierend auf dem aggregierten, relativen EAI pro Pixel können wir dann auf weitere Metriken schliessen. Wir können sie beispielsweise wieder aggregieren und dann mit EAI_mean im Departement x relative Ackerfläche x Fläche Departement berechnen wie viel Ackerfläche jährlich in jedem Departement beschädigt wird.

## Probleme der Berechnung welcher Akteur welchen Schaden übernimmt über EAI

Basierend auf unseren Tests scheint diese Methode ganz gut für die Aggregation zu funktionieren. Was uns aber Schwierigkeiten bereitet hat, ist das Einbauen der Versicherungsstruktur in diese Berechnung. Da diese auf prozentualen Schwellenwerten (20% und 50% Schaden) beruht, schien es logisch jeweils zu schauen, wo bzw. wie oft ein EAI eine solche Schwelle überschreitet. Dies liefert jedoch ein stark verzerrtes Bild und schafft es nicht die wichtigsten Konzepte der Versicherungsdynamik abzubilden. Den Nutzen den Versicherungen generieren, basiert nicht auf mittleren Schäden sondern extremen Ereignissen. Es geht nicht darum Feldern mit über 20% EAI zu versichern, sondern solche, die nur in selteneren Fällen grössere Schäden erleiden. Sich zu fragen, ob in einem durchschnittlichen Jahr der Schaden den Schwellenwert überschreitet ergibt wenig Sinn. Es führt dazu, dass laut Berechnungen, die Bauern den Grossteil der Schäden bezahlen müssten.

Eine deutliche Erweiterung der Methode müsste versuchen, zu schätzen, wie viel Prozent der Jahre, der Schaden die Schwellenwerte überschreitet und wie viel Schaden dabei erwartet wird. Dadurch könnte dann auf einem räumlich aggregierten Level, geschaut werden, wie die Verteilung der Schäden aussieht.

## Ansatz: Yearsets (Basis für Resultate)

> Siehe Notebook 0520_yearset-scenarios

### 1. Relativer Impact pro Hazard

Für jeden Hazard wird eine CLIMADA-Impact-Rechnung mit einer einheitlichen Exposure (alle Werte = 1) durchgeführt.  
Das Ergebnis ist ein **relativer Schaden pro Pixel und Event**, unabhängig von absoluten Werten.

### 2. Zusammenführen der Hazards

Die Impacts aller Hazard-Typen werden zu einem **synthetischen Hazard** zusammengeführt:
- Kombination aller Events
- Intensitäten entsprechen relativen Schäden (Hazard-Typ wird irrelevant)
- Umwandlung zurück in ein CLIMADA-Impact-Objekt

### 3. Simulation jährlicher Schäden

Zur Abschätzung der jährlichen Schadensverteilung werden **CLIMADA Yearsets** verwendet:
- Events werden basierend auf Wahrscheinlichkeiten kombiniert
- Der jährliche Schaden wird berechnet als:

$$
Impact(Location, Year) = 1 - \prod_{\text{Events im Jahr}} \left(1 - Impact(Location, Event)\right)
$$

Eigenschaften:
- Schäden sind **nicht additiv**
- Gesamtimpact ist auf **100% begrenzt**
- Folgeereignisse wirken nur auf verbleibende ungeschädigte Anteile

### 4. Aufteilung der Schäden

Für jedes simulierte Jahr wird der Schaden verteilt auf:
- Landwirt:innen
- Versicherungen
- Staat

Die Aufteilung basiert auf:
- Schadensschwellen (gemäß französischem Ernteversicherungssystem)
- Lokaler Versicherungsabdeckung

### 5. Erwarteter jährlicher Schadensanteil

$$
Expected\ Share(Location, Actor) =
\frac{\sum (\text{Schaden} \times \text{Anteil})}{\text{Anzahl Jahre}} \times Exposure
$$

Mit:
- **Schaden** = relativer jährlicher Schaden
- **Anteil** = vom Akteur übernommener Schaden
- **Exposure** = landwirtschaftliche Fläche pro Pixel

**Output:**
- Drei Karten (je ein Akteur)
- Zeigen: erwartete beschädigte Fläche pro Jahr, die finanziert wird

### 6. Räumliche Aggregation

- Aggregation auf **Departement-Ebene** durch Mittelwertbildung
- Nationale Werte: gewichtete Summe nach Fläche

### 7. Versicherungsszenarien

Zur Simulation erhöhter Versicherungsdichte:

$$
Insurance_{new} = Insurance_{current} + (1 - Insurance_{current}) \times Scaling\ Factor
$$

- Erhöht Abdeckung vor allem in niedrig versicherten Regionen
- Beeinflusst nur die **Kostenverteilung**, nicht den Schaden


---

# Überblick über Repository

Unser Workflow sah etwa so aus:

1. Funktionen in Jupyter Notebooks entwickeln (siehe in Ordner "notebooks") und testen.
2. Fertige Funktion in src Directory verschieben (siehe Ordner "src").
3. In einem Notebook den ganzen Ablauf durchrechnen (siehe in Ordner "notebooks", zB 0424_yearset-scenarios.ipynb)

Die wichtigsten Funktionen werde ich kurz beschreiben siehe "0424_yearset-scenarios.ipynb".

## get_haz_dict() in data_hazard.py

Damit es einfach ist neue Hazards hinzuzufügen, haben wir ein modulares System entwickelt. Für jeden Hazard wird eine Funktion definiert, die Hazardobjekt und zugehöhrige Impact Function definiert und in einem standartisierten Format ausgiebt. "get_haz_dict" sammelt dann all diese Outputs und bereitet ein Dictionary für weitere Schritte vor.

## get_exposure() in data_exposure.py

Alle Daten die wir auf Departementsebene haben (relative Landwirtschaftsfläche, Grösse Departement, aktuelle Versicherungsabdeckung) ist in einem CSV File gespeichert. "get_exposure" lädt dieses CSV File und macht daraus ein CLIMADA Exposure Objekt. Hierfür kombiniert es die Daten aus dem CSV File mit Polygonumrissen der Departement. Zusätzlich fügt die Funktion noch Spalten mit dem IDs der Impactfunctions ein.

## eai_helpers.py

- comp_impact(): Aggregiert Hazards über deren EAI pro Pixel
- comp_who_pays(): Berechnet Verteilung des Schadens basiert auf relativem Schaden und Versicherungsabdeckung

## yearset_helpers.py

- comp_who_pays_dense(): Vektorisierte Version von comp_who_pays() welche für den neuen Workflow mit Sparse und COO Matrizen funktioniert.

## scenario_helpers.py

- comp_insurance(): Berechnet Versicherungsabdeckungsszenarios
- plot_scenario(): Plottet absolute Versicherungsabdeckungs und Who-Pays Werte
- plot_difference(): Plottet absolute Versicherungsabdeckung und Differenzen von Who-Pays Werten zwischen zwei Szenarios

## helpers.py

- agg_to_departement(): Counterpart zu CLIMADAs u_lp.exp_geom_to_pnt()

---

# Datengrundlage

| Kategorie                 | Beschreibung                                                                 | Quelle |
|--------------------------|-----------------------------------------------------------------------------|--------|
| **Hitze (Hazard)**       | Tägliche Maximaltemperaturen (Apr–Sep, 1990–2024), ERA5                     | https://cds.climate.copernicus.eu/datasets/derived-era5-single-levels-daily-statistics |
| **Hitze (Impact)**       | Einfluss von Hitzestress auf Maiserträge in Frankreich                      | https://pmc.ncbi.nlm.nih.gov/articles/PMC3599478/ |
| **Niederschlag (Hazard)**| Tägliche Niederschlagssummen (Apr–Sep, 1990–2024), ERA5                     | https://cds.climate.copernicus.eu/datasets/derived-era5-single-levels-daily-statistics |
| **Niederschlag (Impact)**| Plausibel modellierte Impact-Funktion                                       | Eigene Herleitung |
| **Hagel (Hazard)**       | 330-jähriger probabilistischer Ereignissatz (Europa, Hagelgröße)            | CLIMADA API |
| **Hagel (Impact)**       | Synthese aus wissenschaftlichen Studien                                     | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0210787 <br> https://journals.ametsoc.org/view/journals/apme/10/2/1520-0450_1971_010_0270_hcrtcd_2_0_co_2.xml <br> https://www.jstage.jst.go.jp/article/agrmet1943/34/2/34_2_65/_article |
| **Flussüberschwemmung (Hazard)** | Historische Überflutungsflächen (2002–2018, 200m Auflösung)         | CLIMADA API |
| **Flussüberschwemmung (Impact)** | Impact-Funktion für Landwirtschaft                                  | https://climada-petals.readthedocs.io/en/v6.0.0/_modules/climada_petals/entity/impact_funcs/river_flood.html |
| **Landwirtschaftsfläche (Exposure)** | Anteil landwirtschaftlicher Nutzung pro Pixel (%)            | https://www.insee.fr/fr/statistiques/7728859?sommaire=7728903 |
| **Versicherungsabdeckung** | Versicherungsrate pro Departement in Frankreich                          | https://www.banque-france.fr/en/publications-and-statistics/publications/crop-insurance-subsidies-limited-impact-subscription-rates |


**Hinweis:**  
Ein Schwerpunkt lag auf der Kombination mehrerer Hazards. Die Kalibrierung einzelner Impact-Funktionen stellt daher eine potenzielle Schwäche der Analyse dar.