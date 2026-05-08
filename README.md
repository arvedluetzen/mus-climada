# mus-climada

Quantitative Analysis for Group Work in FS2026 "Praktikum Mensch- und Umweltsysteme" at ETH Zürich

## Background

---

# Beschreibung der Quantitativen Analyse

Eine "klassische" CLIMADA Analyse ergab mit unserem Thema von Versicherungen wenig Sinn. Die Versicherungsabdeckung zu verändern, hat weder einen Einfluss auf die Vulnerability noch auf Hazard oder Exposure (Auf jeden Fall nicht direkt). Die Frage, die wir zu beantworten versuchen ist wie sich die Kostenlast zwischen den Akteuren Bauern, Versicherungen und Staat verteilt, wenn sich die Versicherungsabdeckung ändert. Konzeptionell sollten davon sowohl Bauern als auch Versicherungen profitieren. Dies in einem Modell auszudrücken erfordert folgende Informationen:

- Hazard: Informationen über wetterbedingten Schaden an jedem Ort in Frankreich. In unserem Fall ist jedoch entscheidend, dass die staatlich subventionierte Versicherung 15 verschiedene Hazards abdeckt. Wir müssen also einen Weg finden mehrere zu kombinieren. Dies ist nicht in CLIMADA implementiert. Dies sinnvoll zu machen, ist der zentrale Teil unserer Analyse. Wir betrachten die Auswahl von Hitze, Niederschlag, Hagel und Flussüberschwemmungen.
- Exposure: Um die Verteilung der Hazards mit Landwirtschaftsfläche zu kombinieren, brauchen wir gewisse Informationen, über wo in Frankreich Landwirtschaft betrieben wird. Um diesen Teil der Analyse einfach zu halten, haben wir uns hierbei auf Departementweite Zahlen beschränkt.

Der konzeptionelle Ablauf unserer Analyse bestand also aus den folgenden Schritten:

1. Daten für jeden Hazard einlesen und eine passende Impact Funktion definieren.
2. Einen relativen Impact für jeden Hazard zu berechnen.
3. Die Impacts basierend auf dem Expected Annual Impact (EAI) zusammenrechnen.
4. Den kummulierten Impact nutzen, um zu bestimmen, wer wie viel dieses Schadens übernimmt. In diesem Schritt können Szenarios für veränderte Versicherungsabdeckungen einfliessen.

Wir werden im Folgenden unseren Prozess noch etwas detaillierter beschreiben.

[INSERT FIGURE]

## Akkumulieren der Impacts

Unser Ziel, den akkumulierten EAI zu berechnen, haben wir mit relativen Impacts gerechnet:

1. Mit CLIMADA's ImpactCalc den Impact für jeden Hazard einzeln ausrechnen. Hierbei haben wir einen "Eigen-Exposure" verwendet, bei welchem wir auf der Vorlage des "echten" Exposure Objekts, alle Werte auf 1 gesetzt haben. Dies führt dazu, dass der Output der ImpactCalc rein relativ ist und noch nicht auf eine Exposure skaliert.
2. Die relativen Impacts werden pro Pixel miteinander multipliziert: (1 - EAI_heat) x (1 - EAI_hail) x ... Unser Argument hierfür ist, dass Schäden nicht additiv sind, sondern auf das "zurückbleibende" wirken. Dies ist noch immer eine Starke annahme und vernachlässigt viele reale Interkationen zwischen Hazards (Man denke Beispielsweise wie eine Hitzewelle, die die Böden ausgetrocknet hat, Starkniederschläge verschlimmert, weil Böden weniger bereit sind Wasser aufzunehmen. Auch die Reihenfolge wird nicht in Betracht gezogen.)
3. Basierend auf dem aggregierten, relativen EAI pro Pixel können wir dann auf weitere Metriken schliessen. Wir können sie beispielsweise wieder aggregieren und dann mit EAI_mean im Departement x relative Ackerfläche x Fläche Departement berechnen wie viel Ackerfläche jährlich in jedem Departement beschädigt wird.


## Probleme mit der Berechnung welcher Akteur welchen Schaden übernimmt

Basierend auf unseren Tests scheint diese Methode ganz gut für die Aggregation zu funktionieren. Was uns aber Schwierigkeiten bereitet hat, ist das Einbauen der Versicherungsstruktur in diese Berechnung. Da diese auf prozentualen Schwellenwerten (20% und 50% Schaden) beruht, schien es logisch jeweils zu schauen, wo bzw. wie oft ein EAI eine solche Schwelle überschreitet. Dies liefert jedoch ein stark verzerrtes Bild und schafft es nicht die wichtigsten Konzepte der Versicherungsdynamik abzubilden. Den Nutzen den Versicherungen generieren, basiert nicht auf mittleren Schäden sondern extremen Ereignissen. Es geht nicht darum Feldern mit über 20% EAI zu versichern, sondern solche, die nur in selteneren Fällen grössere Schäden erleiden. Sich zu fragen, ob in einem durchschnittlichen Jahr der Schaden den Schwellenwert überschreitet ergibt wenig Sinn. Es führt dazu, dass laut Berechnungen, die Bauern den Grossteil der Schäden bezahlen müssten.

Eine deutliche Erweiterung der Methode müsste versuchen, zu schätzen, wie viel Prozent der Jahre, der Schaden die Schwellenwerte überschreitet und wie viel Schaden dabei erwartet wird. Dadurch könnte dann auf einem räumlich aggregierten Level, geschaut werden, wie die Verteilung der Schäden aussieht.

---

# Überblick über Repository

Unser Workflow sah etwa so aus:

1. Funktionen in Jupyter Notebooks entwickeln (siehe in Ordner "notebooks") und testen.
2. Fertige Funktion in src Directory verschieben (siehe Ordner "src").
3. In einem Notebook den ganzen Ablauf durchrechnen (siehe in Ordner "notebooks", zB 0424_pipeline-scenarios.ipynb)

Die wichtigsten Funktionen werde ich kurz beschreiben siehe "0424_pipeline-scenarios.ipynb".

## get_haz_dict() in data_hazard.py

Damit es einfach ist neue Hazards hinzuzufügen, haben wir ein modulares System entwickelt. Für jeden Hazard wird eine Funktion definiert, die Hazardobjekt und zugehöhrige Impact Function definiert und in einem standartisierten Format ausgiebt. "get_haz_dict" sammelt dann all diese Outputs und bereitet ein Dictionary für weitere Schritte vor.

## get_exposure() in data_exposure.py

Alle Daten die wir auf Departementsebene haben (relative Landwirtschaftsfläche, Grösse Departement, aktuelle Versicherungsabdeckung) ist in einem CSV File gespeichert. "get_exposure" lädt dieses CSV File und macht daraus ein CLIMADA Exposure Objekt. Hierfür kombiniert es die Daten aus dem CSV File mit Polygonumrissen der Departement. Zusätzlich fügt die Funktion noch Spalten mit dem IDs der Impactfunctions ein.

## comp_impact() in helpers.py

Diese Funktion rechnet den Prozess der vorher beschrieben wurde. Sie berechnet den relativen EAI für jedes Pixel und Hazard und aggregiert diese durch multiplizieren.

## comp_scenarios() in scenario_helpers.py

Das Ziel dieser Analyse ist es, verschiedene Versicherungsabdeckungsgrade zu vergleichen. Deshalb berechnet diese Funktion für verschiedene "Scaling Factors" aus, welcher Akteur wie viel der beschädigten Fläche übernehmen wird. Dies macht sie wie folgt:

1. comp_insurance: Basierend auf einem Scaling Factor berechnet die Funktion die neue Versicherungsabdeckung. Bei der Methode "coverage" wächst diese mehr in Departementen, wo der Abdeckungsgrad aktuell besonders tief ist.
2. comp_who_pays: Basierend auf Versicherungsabdeckung und relativen Schäden pro Pixel rechnet die Funktion aus, welcher Akteur wie viel des Schadens übernimmt.
3. agg_to_departement: Die vorherigen Berechnungen wurden alle auf Pixelebene gemacht, um die inhomogenität der Wetterereignisse abbilden zu können und um miteinzubeziehen, dass Versicherungen bei kleinskaligen Verlusten greifen und nicht nur wenn der mittlere Schaden eines Departements einen Schwellenwert erreicht.