# Disjunktiv und Edge-Finding – Schlüsse über Maschinen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-disjunktiv-edge-finding-demo.streamlit.app/)** -->

Stück der Linie **SAT und Constraint Programming** (CP-Arm) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Anders als die Fall-Demos zeigt sie **eine Frage der Constraint-Programmierung** an einem wachsenden Beispiel: Aus der Bedingung „höchstens eine Operation je Maschine“ wird **Suche**. Wie viel Suche, hängt davon ab, wie viel die Propagation nach jeder Entscheidung schon ausschließt. Das Vehikel ist der **Job Shop** (Aufträge mit fester Maschinenfolge, Ziel: kleinster Makespan); Verwandte sind [job-shop-demo](https://github.com/sebastian-hanisch/job-shop-demo), [shifting-bottleneck-demo](https://github.com/sebastian-hanisch/shifting-bottleneck-demo) und [job-shop-tabu-demo](https://github.com/sebastian-hanisch/job-shop-tabu-demo), die dasselbe Modell mit Heuristiken lösen; hier geht es um die **Propagation im Inneren**, mit Beweis bis zum Optimum.

## Warum dieses Problem

Auf einer Maschine gilt für je zwei Operationen „a vor b **oder** b vor a“, eine **Disjunktion**. Reine Vorrangpropagation (die Kanten der Auftragsketten und der schon beschlossenen Paare) sieht diese Bedingung nicht und muss sie durch Verzweigen entdecken. Zwei Schlüsse sehen sie früher: der **Paar-Test** (passt „a vor b“ noch, passt „b vor a“ noch?) und das **Edge-Finding** (passt die Summe der Dauern einer ganzen Menge von Operationen in ihr Zeitfenster?). Die Demo zählt die **Suchknoten** bis zum bewiesenen Optimum bei jeder Stufe und fragt: Wo sitzt die Ersparnis, im Median oder im Tail?

## Modell

- **Instanz.** Aufträge mit je einer festen Folge von Operationen; jede Operation braucht eine Maschine für eine ganzzahlige Dauer (Dauern 1 bis 9 bei den Zufallsinstanzen). Zufalls-Job-Shops: jeder Auftrag besucht jede Maschine genau einmal in zufälliger Reihenfolge (eigener SplitMix64-Generator, deshalb auf jeder Plattform dieselben Instanzen). Das **Handbeispiel** hat 3 Aufträge, 3 Maschinen und Dauern 1 oder 2.
- **Fenster.** Für den Horizont H („Makespan höchstens H“) hat jede Operation ein Fenster aus frühestem Start `est` und spätestem Start `lst`; `lct = lst + Dauer`. Der **Pflichtteil** `[lst, est + Dauer)` ist der Zeitraum, in dem die Operation auf jeden Fall läuft.
- **Stufen der Propagation** (jede enthält die vorige): **0** nur Vorrang; **1** + Paar-Test; **2** + Edge-Finding (Intervallfassung); **3** (Erweiterung) + Edge-Finding mit Θ-Λ-Baum statt der Intervallfassung. Erklärtabelle der Stufen (was sie sieht, was nicht) in der App.
- **Suche.** Verzweigen auf das offene Paar (weder durch Kanten noch durch Ketten geordnet) mit der kleinsten Spielraumsumme, bei Gleichstand das kleinste Paar, das Paar mit früherem `est` zuerst. Die Suche beginnt mit der Schranke eines Dispatching-Plans (früheste Startzeit, dann kürzeste Dauer); nach jedem gefundenen Plan sinkt H auf Makespan − 1, bis kein besserer Plan mehr existiert.
- **Aufwand.** Gezählt werden **Suchknoten** (Zustand nach der Propagation, Wurzel eingeschlossen), Fehlschläge, Propagationsrunden und Edge-Finding-Aufrufe, **nie Sekunden**. Ein Knotenbudget bricht ab; abgebrochene Läufe zählen mit dem Budget (untere Schranke).
- **Edge-Finding ist eine eigene Nachbildung** des in der Literatur beschriebenen Verfahrens, aus dem Gedächtnis geschrieben; die **Quellen sind nicht gelesen** (siehe Einordnung). Mathematik und Annahmentabelle: Expander **📐 Mathematische Formulierung** und Abschnitt **🚧 Wo die Annahmen enden** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| Mini-CP: Fenster, Vorrang, Paar-Test, Edge-Finding (Intervall), Suche, Zähler, Spur, Prüfer | `dje_algorithm.py` | Stufen 0 bis 2; Entscheidungsfassung (`entscheide`) und Optimierung (`loese`) |
| Θ-Λ-Baum, Edge-Finding und Überlastprüfung (Erweiterung) | `dje_baum.py` | Stufe 3 |
| Instanzen, Handbeispiel, Dispatching-Plan | `dje_scenario.py` | `make_jobshop`, `HANDBEISPIEL`, `spt_plan` |
| SplitMix64 | `dje_rng.py` | **wörtlicher Auszug** (`MASK` und Klasse) aus reduktionskette-demo/red_scenario.py (Commit ba24648); Regressionstest auf feste Werte und auf Gleichheit mit dem Original |
| Aufzählung aller Maschinenreihenfolgen | `dje_aufzaehlung.py` | der exakte Gegenentwurf für das Handbeispiel (216 Kombinationen) |
| Messreihen, Zählungen, Verdikte | `dje_evaluation.py` | alle Verdikte als reine Funktionen |
| Vorgerechnete Messreihen | `dje_sweeps.json` | Messskript `tools/messung_sweeps.py`; in der App ausdrücklich „vorgerechnet, nicht live“ |

Experimente in der App: **Das Handbeispiel Schritt für Schritt** (Fensterbalken mit Pflichtteil, Schieberegler durch jeden Schritt mit Begründung), **Die Stufen im Vergleich** (vorgerechnete Verteilungen auf 5 × 5 und 6 × 6, dazu eine Einzelinstanz live mit Knotenbudget und Gantt-Diagramm des Plans), **Der Tail** (eingefrorener 8 × 8-Fall mit Knopf zum Nachrechnen), **Woher die Ersparnis kommt** (Fehlschläge nach Ursache, Kanten, Verengungen; Horizont-Hypothese; Beweis der Pflichtteil-Sicht), **Gleicher Schluss, gleiche Knoten** (Erweiterung: Θ-Λ-Baum).

## Befunde (gemessen, keine Behauptungen)

Messreihen: Zufalls-Job-Shops mit Dauern 1 bis 9, **10 feste Instanzen 5 × 5** (Zufalls-Seeds 1 bis 10, Budget 50.000), **20 feste Instanzen 6 × 6** (Zufalls-Seeds 1 bis 20, Budget 50.000), **10 feste Instanzen 8 × 8** (Zufalls-Seeds 1 bis 10, Budget 100.000), gemessen in `dje_sweeps.json` mit `tools/messung_sweeps.py`; jedes bewiesene Optimum stimmt mit OR-Tools CP-SAT überein (150 von 150). Zahlen aus dieser Messung stehen in `tests/test_claims.py`; die Zahlen früherer Messungen mit einem anderen Zufallsgenerator gelten nicht (siehe Korrekturen).

| Frage | Befund |
|---|---|
| **Das Handbeispiel** (3 × 3) | Aufzählung aller Maschinenreihenfolgen: 6³ = 216 Kombinationen, davon 132 zulässig (ohne Kreis); optimaler Makespan 8, von 4 Kombinationen erreicht. Horizont 7 (Beweis, kein Plan): 17 / 3 / 1 / 1 Knoten bei Stufe 0 / 1 / 2 / 3 (9 / 2 / 1 / 1 Fehlschläge). Horizont 8 (erste Lösung): 10 / 2 / 2 / 2 Knoten, 0 Fehlschläge. Die Stufe 2 beweist „kein Plan mit Makespan 7“ an der Wurzel: Auf Maschine 1 hat das Fenster [3, 7] die Länge 4, die drei Operationen brauchen zusammen 5, obwohl **jedes Paar** passt (`test_ueberlast_auf_maschine_1_ist_der_beweis`, `test_suchknoten_bei_horizont_7_von_hand`, `test_claim_handbeispiel`). |
| **Der Paar-Test macht den Sprung** | Median der Knoten bis zum bewiesenen Optimum, Stufe 0 gegen Stufe 1: **5 × 5: 198 gegen 35 (5,7-fach), 6 × 6: 1.864 gegen 151 (12,3-fach)**; Summe über die Instanzen 3.004 gegen 404 (5 × 5) und 106.886 gegen 3.340 (6 × 6). Gilt für diese Verzweigungsregel und Startschranke, Instanzen bis 6 × 6 (`test_claim_paar_test_median`). |
| **Edge-Finding im Median: wenig bei 5 × 5 und 6 × 6, ein Drittel weniger bei 8 × 8** | Median Stufe 1 gegen Stufe 2: **5 × 5: 35 gegen 35**, 6 × 6: 151 gegen 138 (9 % weniger als Stufe 1), 8 × 8: 891 gegen 599 (33 % weniger). Stufe 2 hat weniger Knoten als Stufe 1 in 6 von 10 (5 × 5), 14 von 20 (6 × 6) und 10 von 10 (8 × 8) Instanzen, gleich viele in 4, 5 und 0, **mehr in einer einzigen** (6 × 6, Zufalls-Seed 9: 251 gegen 247 Knoten); mehr Schluss heißt also nicht in jeder Instanz weniger Suche (`test_claim_edge_finding_im_median`). |
| **Edge-Finding im Tail: mehr** | 90-%-Wert und Maximum der Knoten, Stufe 0 / 1 / 2: 5 × 5: 401 / 97 / 79 und 1.231 / 97 / 95; 6 × 6: 12.935 / 259 / 249 und 43.007 / 603 / 269; 8 × 8 (nur Stufe 1 / 2): 10.753 / 1.107 und 15.615 / 5.521. Der Tail schrumpft in 5 × 5 und 6 × 6 vor allem durch den **Paar-Test** (6 × 6: Maximum 43.007 gegen 603); Edge-Finding senkt das Maximum auf 269 und im 8 × 8 den 90-%-Wert von 10.753 auf 1.107 (`test_claim_tail`). |
| **Der eingefrorene Extremfall** | 8 × 8, Zufalls-Seed 12 (unter den Seeds 1 bis 60 der Fall mit dem größten Abstand, im Rückblick gewählt): **Stufe 1 bricht beim Budget von 100.000 Knoten ab** (untere Schranke), Stufe 2 und Stufe 3 beweisen das Optimum 75 in **285 Knoten**. Im Seed-Scan erreichte Stufe 1 das Budget von 20.000 Knoten in **1 von 60** Seeds, in den 10 Seeds der Messreihe 8 × 8 bei keinem (`test_claim_tail_eingefroren`). |
| **Wo der Mengenschluss wirkt: Beweis der Unerfüllbarkeit gegen erste Lösung** | Summe der Knoten Stufe 1 gegen Stufe 2 (bei Horizont = Optimum − 1 ist die Aufgabe unerfüllbar und der ganze Baum wird durchsucht, bei Horizont = Optimum nur bis zur ersten Lösung; Horizont und Aufgabenart sind hier nicht zu trennen): Beweis bei Horizont = Optimum − 1: **5 × 5: 40 gegen 14 (65 % weniger), 6 × 6: 710 gegen 216 (70 % weniger)**; erste Lösung bei Horizont = Optimum: 5 × 5: 78 gegen 55 (29 % weniger), 6 × 6: 306 gegen 221 (28 % weniger). Beim Beweis der Unerfüllbarkeit (Horizont = Optimum − 1) spart Stufe 2 gegenüber Stufe 1 65 / 70 %, bei der Suche der ersten Lösung (Horizont = Optimum) 29 / 28 %; die Hypothese des Plans (Edge-Finding wirkt vor allem bei engem Horizont) lässt sich damit nicht von „vor allem beim Beweis“ trennen (`test_claim_horizont`). |
| **Welcher Schluss findet die Fehlschläge** (6 × 6, Summe über 20 Instanzen) | Stufe 1: 1.552 Fehlschläge, davon 1.286 durch Vorrang (leeres Fenster) und 266 durch den Paar-Test; Stufe 2: 1.265 Fehlschläge, davon 1.143 durch Vorrang, 50 durch den Paar-Test und 72 durch Edge-Finding. Der Paar-Test setzt 16.703 Kanten (Stufe 1; Kanten, die schon aus den Auftragsketten folgen, mitgezählt), Edge-Finding verengt in Stufe 2 3.600 Fenster. In beiden Stufen ist die große Mehrheit der Fehlschläge ein leeres Fenster durch Vorrang; der Paar-Test und das Edge-Finding melden selbst nur 266 beziehungsweise 122 (50 + 72) Fehlschläge. Ihre Wirkung liegt demnach vor allem in den gesetzten Kanten und verengten Fenstern, die die Suche später auf leere Fenster stoßen lassen (Deutung, nicht gemessen) (`test_claim_ursachen`). |
| **Gleicher Schluss, gleiche Knoten (Erweiterung)** | Stufe 3 (Θ-Λ-Baum) hat in **40 von 40** Instanzen (5 × 5, 6 × 6, 8 × 8) dieselbe Knotenzahl wie Stufe 2. Auf **4.000** zufälligen Einzelmaschinen-Fenstern (3 bis 6 Operationen) haben Intervallfassung und Baum denselben Fixpunkt (1.333 Fälle ohne Fehlschlag) oder denselben Fehlschlag (2.667 Fälle) in 4.000 von 4.000 Fällen. Im Test stimmt der Baum außerdem mit der Aufzählung aller Mengen Ω überein (`test_claim_baum`, `tests/test_oracle_baum.py`). |
| **Pflichtteil-Sicht** | Auf 10.000 Zufallsfenstern zweier Operationen überlappen die Pflichtteile in 805 Fällen, und in **allen 805** ist der Paar-Test unmöglich (weder „a vor b“ noch „b vor a“ passt); in weiteren 358 Fällen scheitert er **ohne** überlappende Pflichtteile. Der Beweis der Aussage steht in der App (`test_claim_pflichtteil`). |
| **Presets** | Handbeispiel Horizont 7: 1 Knoten (Stufe 2) gegen 17 (Stufe 0); Handbeispiel Horizont 8: 10 / 2 / 2 Knoten für Stufe 0 / 1 / 2 (`tests/test_presets.py`). |

## Ehrliche Grenzen

- **Eine Verzweigungsregel, eine Startschranke, kleine Instanzen.** Die Knotenzahlen gelten für diese Regel und diesen Dispatching-Plan als Start, für Dauern 1 bis 9 und Größen bis 8 × 8 mit 10 bis 20 Instanzen je Größe. Sie sagen nichts über Benchmark-Instanzen (Fisher–Thompson, Lawrence) und nichts über 10 × 10 und mehr.
- **Knoten sind keine Rechenzeit.** Die Kosten je Knoten sind nicht gemessen; ein Verfahren mit weniger Knoten ist deshalb nicht belegt schneller. Insbesondere sagt die Demo nichts über die Laufzeit des Θ-Λ-Baums gegen die Intervallfassung.
- **Der Tail ist ein Einzelfall.** Der eingefrorene Fall ist im Rückblick aus 60 Seeds gewählt; Stufe 1 erreichte das Budget von 20.000 Knoten nur in 1 von 60 Seeds. Aussagen über „den Tail“ stützen sich auf 90-%-Werte und Maxima von 10 bis 20 Instanzen je Größe und sind entsprechend unsicher.
- **Edge-Finding ist eine eigene Nachbildung.** „Der Θ-Λ-Baum bringt keine Suchersparnis“ gilt für diese Nachbildung und diese Instanzen, nicht für das Verfahren der Literatur im Allgemeinen. Die Intervallfassung (Stufe 2) benutzt für Ω nur Operationen, die ganz in ein Zeitfenster passen; ihr Fixpunkt stimmt mit der Mengenform (Aufzählung aller Teilmengen) in 300 Testfenstern mit 3 bis 5 Operationen überein und mit dem Θ-Λ-Baum in 4.000 Fenstern mit 3 bis 6 Operationen; für größere Mengen je Maschine ist das nicht geprüft.
- **Nur Kapazität 1.** Der Paar-Test und das Edge-Finding dieser Demo gelten für Maschinen, die eine Operation zugleich bearbeiten. Kumulative Ressourcen (Kapazität größer 1) brauchen andere Schlüsse und sind nicht Gegenstand.
- **Kein Lernen.** Die Suche lernt nichts aus Fehlschlägen (kein Klausellernen); das ist ein eigenes Thema.
- **Die Zufallsinstanzen sind Job Shops mit je einer Operation pro Auftrag und Maschine.** Andere Strukturen (Fließfertigung, Open Shop, Rüstzeiten) sind nicht gemessen.

## Befunde und Korrekturen gegenüber dem Plan

- **Neue Zahlen statt der früheren Messung.** Eine Messung vor dem Bau (Python-Zufallsgenerator, andere Instanzen) nannte für 5 × 5 / 6 × 6 Mediane von 203 / 32 / 27 und 1.231 / 110 / 99 für Stufe 0 / 1 / 2; mit SplitMix64-Instanzen sind es 198 / 35 / 35 und 1.864 / 151 / 138. Die Richtung bleibt (der Paar-Test macht den Sprung, das Edge-Finding spart im Median wenig), die Faktoren (6,3 und 11 in der früheren Messung) sind jetzt 5,7 und 12,3. Die Zahlen der früheren Messung gelten als überholt.
- **Der Tail ist seltener als in der früheren Messung.** Diese fand auf 10 Instanzen 8 × 8 einen Abbruch der Stufe 1 bei 300.000 Knoten; hier bricht Stufe 1 in den 10 Seeds der Messreihe bei 100.000 Knoten nie ab, und im Scan über 60 Seeds erreicht sie ein Budget von 20.000 Knoten nur einmal. Der Befund „Edge-Finding rettet den Tail“ bleibt, aber als Einzelfall (285 Knoten gegen mindestens 100.000) und als Verschiebung des 90-%-Werts, nicht als Regel.
- **Hypothese des Plans: Richtung bestätigt, Ursache nicht getrennt:** Der Mengenschluss spart beim Beweis der Unerfüllbarkeit (Horizont = Optimum − 1) mehr Knoten als bei der Suche der ersten Lösung; Horizont und Aufgabenart wechseln dabei zusammen (siehe Befunde).
- **Handbeispiel unverändert:** alle Zahlen des Plans (216 / 132 / 8 / 4; 17 / 3 / 1 / 1; 10 / 2 / 2 / 2) reproduzieren sich im Bau.
- **Die Erweiterung ist nur zum Teil gebaut:** Stufe 3 (Θ-Λ-Baum) ist umgesetzt, die im Plan genannte Stufe 4 (Detectable Precedences, Not-first/Not-last) nicht.
- **Kanten des Paar-Tests mitgezählt, auch wenn sie aus den Ketten folgen.** Der Paar-Test prüft nur direkte Kanten, nicht ihre transitive Hülle; die Zahl der „Kanten“ ist deshalb eine obere Schranke für die Zahl neuer Ordnungsentscheidungen.

## Bewusst nicht umgesetzt

- **Detectable Precedences und Not-first/Not-last** (Stufe 4 der Erweiterung): in einer früheren Messung des Autors (nicht Teil dieses Repos, hier nicht nachprüfbar) sparten sie in der Suche im Median nichts; nicht gebaut.
- **Kumulative Ressourcen** (Timetabling mit Profil der Pflichtteile, Energie-Überlastprüfung): ein eigenes Thema; hier nur die Pflichtteil-Sicht bei Kapazität 1.
- **Lernen aus Fehlschlägen (Lazy Clause Generation):** eigenes Thema der Linie.
- **Benchmark-Instanzen und andere Verzweigungsregeln:** nicht gemessen.
- **PDF-Export:** nicht gebaut; die Experimente zeigen ihre Ergebnisse in der App.

## Verifikation

- **Kern:** jede Einheit gegen Handrechnung am Handbeispiel (`tests/test_algorithm.py`): Vorlauf und Restdauer, Fenster für H = 7 und 8, die vier Kanten des Paar-Tests, der Edge-Finding-Schluss `lst(1,0) = 1`, die Überlast 3 + 5 = 8 > 7, Suchknoten 17 / 3 / 1 / 1 und 10 / 2 / 2 / 2, Fehlschläge nach Ursache; Randfälle (`tests/test_edge_cases.py`): n = 1, n = 2, Gleichstand in der Verzweigung, Horizont gleich der Kettenlänge, Budget auf der Grenze.
- **Orakel** (`tests/test_oracle_disjunktiv_edge_finding.py`, `tests/test_oracle_baum.py`): das Optimum jeder Stufe gegen die **Aufzählung aller semiaktiven Pläne** und die Aufzählung aller Maschinenreihenfolgen (3 × 3, 2 × 4, 4 × 2, 3 × 2; 40 Seeds je Form) und gegen **OR-Tools CP-SAT** (NoOverlap; 4 × 4 und 5 × 5, 20 Seeds); **Solidität**: jeder Plan mit Makespan höchstens H liegt nach jeder Stufe in den Fenstern, jede Kante des Paar-Tests gilt in jedem dieser Pläne; Fenster nach Stufe 2 ⊆ nach Stufe 1 ⊆ nach Stufe 0 (60 Instanzen); idempotent und monoton im Horizont (30 Instanzen); Umnummerierung der Maschinen ändert das Optimum nie (25 Instanzen); Skalieren der Dauern mit 2 und 3 skaliert den Makespan (15 Instanzen); „Pflichtteil-Überlappung ⇒ Paar-Test scheitert“ auf 10.000 Zufallsfenstern; Θ-Λ-Baum gegen die Aufzählung aller Mengen Ω, Solidität gegen die Aufzählung aller Lösungen einer Maschine, Intervallfassung gegen Baum gegen Mengenform. Im Repo laufen kleine Fassungen; der **große Lauf im Scratch-Ordner** (nicht im Repo) fand **0 Abweichungen**: 1.200 Läufe (300 Instanzen der Formen 3 × 3, 2 × 4, 4 × 2, je alle vier Stufen) gegen die Aufzählung, dazu 2.400 Solidität-Prüfungen (Horizont Optimum und Optimum + 1), und 860 Läufe gegen CP-SAT (40 Instanzen 4 × 4 und 100 Instanzen 5 × 5 mit je vier Stufen, 100 Instanzen 6 × 6 mit Stufe 1 bis 3).
- **Zweig-Test:** auf dem Handbeispiel unterscheiden sich Stufe 0, 1 und 2 in den Knoten (17 / 3 / 1); keine Spalte der Messreihen ist konstant.
- **Messreihen** (`tests/test_sweeps.py`): die JSON-Datei gegen eine Neuberechnung (5 × 5 und 6 × 6 alle Stufen, 8 × 8 die Instanzen mit höchstens 800 Knoten (5 Läufe der Stufe 1, 7 der Stufe 2), der eingefrorene Fall mit Stufe 2; allein im Messskript laufen der Seed-Scan, die größeren 8 × 8-Läufe und Stufe 1 des eingefrorenen Falls) und gegen die Optima von CP-SAT.
- **Kopie** (`tests/test_rng.py`): der SplitMix64-Auszug ist wörtlich gleich dem Original, solange es im Portfolio-Ordner liegt; feste Werte für Seed 0.
- **Verdikte** als reine Funktionen, jede Zahl im Text an handgesetzten Werten (`tests/test_verdicts.py`); **Claims:** jede Zahl dieser README (`tests/test_claims.py`).
- **Presets:** vollständig, gültige Werte, paarweise verschieden, erstes Preset gleich Standard, die Handbeispiel-Presets halten ihre Hilfe (`tests/test_presets.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button einschließlich der beiden Live-Läufe, jeder Regler am Minimum und Maximum, alle sechs Kombinationen aus Horizont und Stufe bis zum letzten Schritt), Layout (Schnellstart in der Seitenleiste, fester Kopf, Hervorhebung), Footer, Laufzeit-Importe.
- **Browser:** Standardansicht mit Fensterbalken, Schritt-für-Schritt-Ansicht (Sprung zum letzten Schritt), Messreihen, Live-Lauf der Einzelinstanz (5 × 5) und Live-Nachrechnen des eingefrorenen Falls im Browser geprüft; keine Konsolenmeldung, auf Telefonbreite (375 Pixel) kein seitliches Scrollen der Seite. Nicht geprüft: dunkles Design, echter Mausklick in den Plotly-Diagrammen (die Diagramme sind nicht anklickbar).

## Einordnung und Quellen

Edge-Finding und der Θ-Λ-Baum sind Verfahren der Constraint-Programmierung für unäre Ressourcen (als Urheber werden in der Literatur Carlier und Pinson sowie Vilím und Mitarbeiter genannt). **Diese Quellen sind für die Demo nicht gelesen**; die Umsetzung ist eine eigene Nachbildung aus dem Gedächtnis, ihre Korrektheit stützt sich auf die Tests gegen die Aufzählung, nicht auf die Quelle. Aussagen der Demo gelten für diese Nachbildung. OR-Tools CP-SAT dient nur als Gegenprobe der Optimalwerte (nur in den Tests und im Messskript, nie in der App); CP-SAT ist ein Hybrid-Löser mit Klausellernen (Perron, Didier und Gay, CP 2023), kein reines Constraint-Programmierungs-Verfahren. SplitMix64 nach der Konvention von Vigna.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Handbeispiel Schritt für Schritt, vier Experimente, Erweiterung, Annahmentabelle, Formeln |
| `dje_algorithm.py` | Mini-CP: Fenster, Vorrang, Paar-Test, Edge-Finding (Intervall), Suche, Spur, Prüfer |
| `dje_aufzaehlung.py` | Aufzählung aller Maschinenreihenfolgen (Handbeispiel) |
| `dje_baum.py` | Θ-Λ-Baum, Edge-Finding und Überlastprüfung (Erweiterung, Stufe 3) |
| `dje_constants.py` | Regler-Grenzen, Messreihen-Parameter, Farben, Presets |
| `dje_evaluation.py` | Statistik der Messreihen, Live-Vergleich, Verdikte |
| `dje_layout.py` | Fester Kopf (Stylesheet) |
| `dje_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `dje_rng.py` | wörtlicher Auszug: SplitMix64 aus reduktionskette-demo |
| `dje_scenario.py` | Instanzen, Handbeispiel, Dispatching-Plan |
| `dje_sweeps.json` | vorgerechnete Messreihen (Messskript `tools/messung_sweeps.py`) |
| `dje_visualization.py` | Plotly-Abbildungen: Fensterbalken, Gantt, Verteilung, Ursachen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur Gegenprobe) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/messung_sweeps.py` | Messskript für `dje_sweeps.json` (braucht OR-Tools) |
| `tests/` | Mini-Instanz von Hand, Orakel, Randfälle, Auswertung, Verdikte, Claims, Messreihen, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
