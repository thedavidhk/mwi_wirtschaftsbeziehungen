# Einleitung

Dieses Script begleitet die Vorlesung *Internationale Wirtschaftsbeziehungen* an der Hochschule Anhalt. Es folgt der Gliederung der Folien, formuliert die zentralen Argumente in zusammenhängendem Fließtext und dient gleichzeitig als Nachschlagewerk für Fragen aus dem Hörsaal. Abbildungen und Daten entsprechen dem Stand der Folien (generiert mit `scripts/generate_figures.py`); Quellenangaben im Text verweisen auf die Literaturdatei `references.bib`.

Die Vorlesung gliedert sich in vier inhaltliche Blöcke. Zunächst geht es um den Zusammenhang zwischen Außenhandel und wirtschaftlicher Entwicklung. Im zweiten Block verschiebt sich der Fokus auf internationale Finanzmärkte. Nach der Pause stehen Wechselkurse, Währungspolitik und Finanzkrisen im Mittelpunkt. Den Abschluss bildet die Versorgungssicherheit in einer zunehmend fragmentierten Weltwirtschaft.

# Außenhandel und wirtschaftliche Entwicklung

## Handel, Armut und Globalisierung

Eine zentrale Frage der Entwicklungsökonomie lautet, ob und unter welchen Bedingungen internationaler Handel zu wirtschaftlicher Entwicklung beiträgt. Zwei empirische Reihen illustrieren, warum diese Frage in der Forschung und Politik so viel Beachtung findet, ohne dass aus Korrelation allein Kausalität folgt.

Die Außenhandelsquote misst den Anteil von Importen und Exporten am Bruttoinlandsprodukt. @fig:trade-share zeigt, dass der Handel seit den 1980er Jahren in vielen Regionen an Bedeutung gewonnen hat, besonders in Entwicklungs- und Schwellenländern. Seit der globalen Finanzkrise 2008/09 ist der Trend jedoch gebrochen: In Industrieländern stagniert die Quote weitgehend, in vielen Entwicklungsländern ist sie sogar rückläufig [@wdi2025; @wto2024].

![Außenhandelsquote nach Einkommensgruppe (Importe + Exporte in Prozent des BIP). Quelle: World Bank WDI.](../images/trade-as-share-of-gdp.svg){#fig:trade-share width=85%}

Parallel dazu ist der Anteil der Bevölkerung in extremer Armut (internationale Armutsgrenze, derzeit 2,15 US-Dollar pro Tag in Kaufkraftparitäten) in allen Einkommensgruppen deutlich gesunken (@fig:poverty). Die Daten für die ärmsten Länder beginnen erst um 2002; dennoch passt der langfristige Rückgang der Armut zeitlich zu Phasen stärkerer Handelsöffnung. Armut hat viele Ursachen — Politik, Konflikte, Klima, institutionelle Qualität —, doch Außenhandel gehört zu den wiederkehrenden Faktoren, die Produktivität und Einkommen beeinflussen [@wdi2025; @rodrik2011].

![Extreme Armut nach Einkommensgruppe (Anteil der Bevölkerung unter 2,15 USD/Tag, KKP). Quelle: World Bank WDI.](../images/poverty-by-income-group.svg){#fig:poverty width=85%}

Zwei Mechanismen verdienen besondere Erwähnung. Erstens macht Handel die Versorgung mit Gütern robuster gegenüber lokalen Schocks: Ein Ernteausfall oder eine regionale Störung muss nicht zwangsläufig in Versorgungsengpässen enden, wenn Importe möglich sind. Zweitens steigt die Produktivität durch Spezialisierung nach komparativen Kostenvorteilen. Um diesen zweiten Kanal zu verstehen, lohnt ein kurzer Blick auf die klassische Handelstheorie.

## Von Smith und Ricardo zur Spezialisierung

Im 17. und 18. Jahrhundert dominierte der Merkantilismus: Exporte galten als Gewinn, Goldreserven als Machtsymbol, Verbraucherinteressen traten zurück. Adam Smith argumentierte dagegen, dass Handel sich lohnt, wenn Länder dort produzieren, wo sie **absolute** Kostenvorteile haben — also wo sie mit gegebenen Ressourcen relativ günstiger produzieren als andere [@smith1776].

David Ricardo präzisierte 1817 das Argument entscheidend: Handel kann beiden Seiten nützen, selbst wenn ein Land in **allen** Gütern absolut effizienter ist. Entscheidend sind **komparative** Kostenvorteile: die relativen Opportunitätskosten der Produktion [@ricardo1817; @krugman2018]. Ricardo illustrierte dies mit dem berühmten Beispiel von Wein und Tuch in Portugal und England.

@tbl:ricardo fasst ein vereinfachtes Zahlenbeispiel zusammen (Arbeitsstunden pro Tonne). Portugal benötigt für Wein 80 und für Tuch 90 Stunden; England 120 bzw. 100 Stunden. Portugal hat in beiden Gütern den absoluten Kostenvorteil. Relativ betrachtet (Tuch pro Tonne Wein) hat Portugal für Wein einen niedrigeren Opportunitätskostenfaktor (0,889 Tuch pro Wein) als England (1,2). Portugal sollte sich auf Wein spezialisieren, England auf Tuch; durch Handel steigt die Gesamtproduktion.

| | Wein (h/t) | Tuch (h/t) | Relativ Wein (Tuch/Wein) | Relativ Tuch (Wein/Tuch) |
|:---|:---:|:---:|:---:|:---:|
| Portugal | 80 | 90 | 0,889 | 1,125 |
| England | 120 | 100 | 1,200 | 0,833 |

: Ricardo-Beispiel: absolute und relative Produktionskosten {#tbl:ricardo}

Dieses Modell ist bewusst stark vereinfacht: Es ignoriert Transportkosten, Wechselkurse, Skaleneffekte, Innovation und Verteilungskonflikte. Es zeigt aber den **statischen** Gewinn aus Spezialisierung. Mittel- und langfristig fallen die Gewinne aus Handel häufig höher aus, weil größere Märkte Skaleneffekte begünstigen, Wettbewerb Technologietransfer erleichtert und ausländische Nachfrage Investitionen anreizt [@krugman2018].

## Asien: Öffnung, Wachstum und Gegenbewegung

@fig:trade-asia und @fig:gdp-asia vergleichen Südkorea, China und Indien. Südkorea öffnete sich bereits in den 1960er und 1970er Jahren stark für den Außenhandel. China begann Ende der 1970er Jahre mit einer graduellen Marktöffnung, blieb aber politisch stark gesteuert. Indien setzte besonders ab den Reformen der frühen 1990er Jahre auf Liberalisierung von Handel und Finanzmärkten [@ahluwalia2002; @kochar2012].

![Außenhandelsquote in ausgewählten asiatischen Schwellenländern. Quelle: World Bank WDI.](../images/trade-as-share-of-gdp-asia.svg){#fig:trade-asia width=85%}

![Reales BIP pro Kopf (Index 1960 = 100). Quelle: World Bank WDI.](../images/gdp-per-capita-asia.svg){#fig:gdp-asia width=85%}

Alle drei Länder illustrieren den engen Zusammenhang zwischen Integration in den Welthandel und langfristigem Aufholwachstum. Seit Mitte der 2000er Jahre lässt sich jedoch eine Deliberalisierungstendenz beobachten: Die Außenhandelsquote kann nicht unbegrenzt steigen, und niedrige globale Zinsen haben in Schwellenländern teils Aufwertungsdruck und finanzielle Instabilität erzeugt. Protektionismus und industriepolitische Schutzmaßnahmen gewinnen wieder an Bedeutung [@rodrik2011; @autor2016china].

## Warum handeln Länder nicht "einfach immer frei"?

Ricardos Modell sagt wenig über **Gewinner und Verlierer** innerhalb eines Landes und kaum über **geopolitische Risiken**. In der Praxis erzeugt Handel Effizienzgewinne, aber auch Verteilungskonflikte: Sektoren verlieren an Schutz, während Verbraucher und exportorientierte Industrien profitieren können. Zudem werden strategische Güter — Energie, Halbleiter, Pharmazeutika, Rüstung — nicht wie Standardgüter behandelt. Abhängigkeiten von geopolitischen Rivalen, Zölle als Druckmittel sowie Klima- und Arbeitsstandards begrenzen die reale Handelsfreiheit [@rodrik2011; @imf2023fragmentation].

Der Economic Policy Uncertainty Index für Handelspolitik misst, wie oft US-Zeitungen über Zölle, Handelskonflikte und Handelsabkommen berichten [@baker2016; @fred2025]. @fig:epu-trade zeigt Spitzen in den Jahren 2018–2019 (Handelskonflikt USA–China) und einen erneuten Anstieg ab 2025 im Kontext der zweiten Trump-Administration [@piie2025tariffs]. Der Index misst **Unsicherheit und mediale Aufmerksamkeit**, nicht den durchschnittlichen MFN-Zollsatz — beides kann auseinanderlaufen.

![Handelspolitische Unsicherheit (monatlicher Index, USA). Quelle: Baker, Bloom, Davis; FRED EPUTRADE.](../images/trade-policy-uncertainty.svg){#fig:epu-trade width=85%}

Damit schließt sich der Bogen zum nächsten Kapitel: Finanzielle Globalisierung und politische Unsicherheit verstärken sich häufig gegenseitig.

# Finanzmärkte und wirtschaftliche Entwicklung

## Kapitalströme und die Realwirtschaft

Während der erste Teil die Gütermärkte betonte, rücken nun internationale Finanzströme in den Vordergrund. Für langfristige Entwicklung bleibt die Produktivität in der Realwirtschaft entscheidend; die Frage ist, wie globale Ersparnisse und Investitionen diese Produktivität beeinflussen [@krugman2018; @eichengreen2008].

@fig:capital-market-1 zeigt ein einfaches Kapitalmarktdiagramm. Auf der vertikalen Achse steht der Zins, auf der horizontalen Achse Ersparnis $S$ und Investition $I$ (vereinfachend in einer gemeinsamen Währung, z. B. US-Dollar). Die Ersparnisfunktion steigt mit dem Zins: höhere Verzinsung fördert Sparen. Die Investitionsfunktion fällt: bei hohen Zinsen lohnen sich weniger Projekte. Im Inland ergibt sich ein Gleichgewicht bei Zins $i^{\ast}$ und Volumen $I^{\ast} = S^{\ast}$.

![Kapitalmarktgleichgewicht (Ersparnis, Investition, internationaler Finanzmarkt).](../images/capital_market1.svg){#fig:capital-market-1 width=75%}

Die horizontale Linie $A$ repräsentiert den Zugang zum **internationalen** Kapitalmarkt zu einem Zins $i' < i^*$. Wenn das Land den Finanzmarkt öffnet, entsteht ein Überschuss an Investitionsnachfrage über inländische Ersparnisse: $I > S$. Kapital strömt ins Land; die Leistungsbilanz weist typischerweise ein Defizit auf (Nettoimport von Kapital). Umgekehrt exportiert ein Land mit hohem inländischen Sparen und wenig Investitionsmöglichkeiten Kapital ins Ausland.

@fig:ca-balances zeigt globale Leistungsbilanzsaldi — die Summe aller Länder sollte in der Theorie nahe null liegen; Messfehler und statistische Asymmetrien erklären Abweichungen. Persistente Überschüsse einzelner Ökonomien (z. B. Deutschland, China in bestimmten Phasen) spiegeln strukturelles Sparen, Währungsinterventionen oder begrenzte Binnenabsorption wider [@wdi2025; @imfsta2025].

![Globale Leistungsbilanzsaldi. Quelle: IMF/WDI.](../images/global_ca_balances.svg){#fig:ca-balances width=85%}

## Indien: Reformen, Direktinvestitionen und Strukturwandel

Indien ist ein eindrückliches Beispiel für die Verbindung von Finanzmarktöffnung und Entwicklung. Bis in die 1980er Jahre war die Wirtschaft stark reguliert und protektionistisch — auch aus historischer Erfahrung mit kolonialer Abhängigkeit [@ahluwalia2002]. Die Balance-of-Payments-Krise 1991 erzwang tiefgreifende Reformen: Abbau von Zöllen und Quoten, Liberalisierung des Bankensektors, Öffnung für ausländisches Kapital.

@fig:india-fdi zeigt den Anstieg der ausländischen Direktinvestitionen (FDI) relativ zum BIP. FDI sind langfristig angelegt: Sie umfassen Beteiligungen an Unternehmen, Fabriken und Infrastruktur, nicht nur kurzfristige Portfolioanlagen [@unctad2025]. Nach 1991 steigen die Quoten kontinuierlich; der Peak von 2009 ist in der Grafik als Ausreißer sichtbar, maskiert aber den graduellen Trend der 1990er Jahre.

![Direktinvestitionen in Indien (Prozent des BIP). Quelle: UNCTAD über World Bank WDI.](../images/india_fdi_gdp.svg){#fig:india-fdi width=85%}

@fig:india-catchup stellt das Pro-Kopf-Einkommen Indiens relativ zu den USA dar. In den 1980er Jahren vergrößerte sich die Lücke; seit den Reformen holt Indien auf — ein bemerkenswertes Ergebnis angesichts starken Bevölkerungswachstums (es handelt sich um **Pro-Kopf**-Größen).

![Pro-Kopf-Einkommen Indien relativ zu den USA. Quelle: World Bank WDI.](../images/india_catch_up.svg){#fig:india-catchup width=85%}

Qualitativ zeigt @fig:india-tech den Anteil mittel- und hochtechnologischer Exporte an den Industrieexporten — ein Indikator für Komplexität und langfristiges Wachstumspotenzial. Seit den frühen 1990er Jahren steigt dieser Anteil stetig. Neben Technologietransfer durch multinationale Unternehmen spielte der verbesserte Zugang heimischer Firmen und Haushalte zum formalen Bankensystem eine Rolle [@kochar2012].

![Medium- und High-Tech-Exporte Indiens (Anteil an Industrieexporten). Quelle: UNIDO/WDI.](../images/india_tech_exports.svg){#fig:india-tech width=85%}

# Wechselkurse, Währungspolitik und Finanzkrisen

## Von Kapitalzuflüssen zur Krise: Thailand

Wenn Globalisierung Entwicklung fördert, warum stockt sie dennoch? Globale Finanzmärkte können lokale Schocks abfedern, eröffnen aber neue Risiken: plötzliche Kapitalumkehr, Wechselkursstress und Verschuldung in Fremdwährung [@eichengreen2008; @fischer1998].

Thailand in den 1990er Jahren illustriert diesen Mechanismus. @fig:thailand-ca zeigt einen ausgeprägten Leistungsbilanzdefizit vor 1997 — das Land importierte netto Kapital und finanzierte Investitionen und Konsum aus dem Ausland. Nach der Krise kehrte sich das Muster schlagartig um: Kapitalabzug, Leistungsbilanzüberschuss, scharfe Kontraktion [@imfsta2025; @corsetti1999].

![Leistungsbilanzsaldo Thailand. Quelle: IMF STA.](../images/thailand_ca_balance.svg){#fig:thailand-ca width=85%}

@fig:capital-market-2 fasst die Dynamik schematisch zusammen. Ausgangslage: $I > S$, Kapitalzuflüsse, Leistungsbilanzdefizit. Steigt der Zins für ausländisches Kapital — etwa wegen einer US-Zinsanhebung oder steigender Risikowahrnehmung —, werden frühere Investitionen unrentabel. Kapital flieht ab; kurzfristig kann $S > I$ gelten. In der Realität verschieben sich die Kurven zusätzlich, wenn Erwartungen, Regulierung oder das Wachstum selbst kollabieren [@corsetti1999; @fischer1998].

![Kapitalmarktdynamik bei Kapitalflucht.](../images/capital_market2.svg){#fig:capital-market-2 width=75%}

Nicht alles investierte Kapital ist langfristiges Eigenkapital. Bankkredite, kurzfristige Portfolioanlagen und fremdwährungsindexierte Schulden reagieren schneller auf Zins- und Wechselkursänderungen als Fabrikinvestitionen.

## Wechselkurse und Verschuldung

Der nominale Wechselkurs gibt an, wie viele Einheiten der Inlandswährung für eine Einheit Auslandswährung gezahlt werden müssen. Eine **Aufwertung** (stärkere Inlandswährung) verbilligt Importe und verteuert Exporte — für exportorientierte Schwellenländer oft ein Wachstumsrisiko. Eine **Abwertung** stützt Exporte, belastet aber Importpreise (Inflation) und erhöht den lokalen Wert von Schulden, die in Fremdwährung denominiert sind [@krugman2018; @eichengreen2008].

@fig:thailand-debt zeigt Thailands Auslandsverschuldung aus zwei Perspektiven: in US-Dollar (Sicht des Weltmarkts) und in Thai Baht (Sicht inländischer Schuldner). Innerhalb eines Jahres kann die Baht-verschuldete Last um fast 60 Prozent steigen, wenn die Währung unter Druck gerät — ein zentraler Kanal der asiatischen Krise 1997 [@imfsta2025; @fischer1998].

![Auslandsverschuldung Thailand (USD vs. THB). Quelle: IMF STA.](../images/thailand_ext_debt.svg){#fig:thailand-debt width=85%}

## Währungspolitik und ihre Grenzen

Zentralbanken können den Wechselkurs beeinflussen. Bei **Aufwertungsdruck** (Kapitalzuflüsse) kaufen sie Devisen und drucken dabei oft inländisches Geld — was Inflation und Kreditboom begünstigen kann. Bei **Abwertungsdruck** verkaufen sie Reserven, um die Währung zu stützen. Diese Intervention ist nur so lange möglich, wie Reserven reichen und Märkte an die Durchhaltbarkeit glauben [@eichengreen2008; @fischer1998].

@fig:thailand-forex zeigt thailändische Währungsreserven und den Baht-Kurs. In der ersten Hälfte der 1990er Jahre stiegen die Reserven durch Devisenkäufe; nach 1997 brachen die Reserven ein, die Währung fiel stark [@imfsta2025].

![Währungsreserven und Wechselkurs Thailand. Quelle: IMF STA.](../images/thailand_forex.svg){#fig:thailand-forex width=85%}

Die Realwirtschaft folgt dem Finanzsektor mit Verzögerung, aber nicht weniger dramatisch. @fig:thailand-gdp zeigt den Einbruch des Pro-Kopf-Einkommens in US-Dollar um rund 40 Prozent; die Erholung verlief über Jahre langsam. Unternehmen und Banken mit Dollar-Schulden konnten ihre Verbindlichkeiten nicht mehr bedienen; Investitionsprojekte wurden gestoppt — aus einer Finanzkrise wurde eine Rezession [@corsetti1999; @fischer1998].

![Pro-Kopf-Einkommen Thailand (aktuelle USD). Quelle: World Bank WDI.](../images/thailand_gdp_per_capita.svg){#fig:thailand-gdp width=85%}

# Versorgungssicherheit in einer fragmentierten Weltwirtschaft

## Ein neues Regime für globale Lieferketten

Globalisierung hat Milliarden Menschen aus extremer Armut gehoben und bleibt ein Hebel für globale Kooperation — von Klimaschutz bis Technologietransfer [@ipcc2023; @rodrik2011]. Seit der COVID-19-Pandemie hat sich die wahrgenommene Fragilität globaler Lieferketten jedoch deutlich verschärft [@baldwin2022; @economist2021supplychains].

@fig:shipping zeigt einen US-Erzeugerpreisindex für Hochseefracht (Proxy für Container-Logistikkosten), indexiert auf 2019 = 100 [@fred2025]. Der Verlauf ist mehr als ein kurzer Schock: Er markiert ein **neues Regime** höherer und volatilerer Logistikkosten.

![Seefracht-Preisindex (Hochsee, 2019 = 100). Quelle: FRED/BLS.](../images/shipping-costs.svg){#fig:shipping width=85%}

Anfang 2020 brachen die Raten mit der Nachfrage ein (Lockdowns). 2021 folgte ein steiler Anstieg durch Güterboom, Hafen- und Containerengpässe. 2022 verstärkten Energie- und Unsicherheitsschocks (u. a. Ukraine-Krieg) den Druck. Seitdem normalisierten sich die Raten vom Peak, blieben aber über dem alten Niveau [@giovanni2022; @imf2023fragmentation].

Hinter dieser Entwicklung stehen mehrere Verschränkungen: lange Spezialisierungsketten verstärken die Wirkung kleiner Störungen; geopolitische Routenrisiken (Suez, Hormus) beeinflussen Energie und Fracht; der Klimawandel belastet Infrastruktur; die Energiewende erzeugt neue Rohstoffabhängigkeiten [@iea2024critical; @usgs2024].

## Geopolitische Engpässe: Suez und Hormus

@fig:suez zeigt das geschätzte Transitvolumen durch den Suezkanal (28-Tage-Durchschnitt, indexiert). Der Einbruch ab Ende 2023 bedeutet nicht, dass der Welthandel um den gleichen Prozentsatz schrumpfte. Der Suez ist Teil der Route durch das Rote Meer und die Straße Bab al-Mandab. Angriffe auf Handelsschiffe und militärische Eskalation veranlassten viele Reedereien zur Umleitung um das Kap der Guten Hoffnung — längere Fahrzeiten, höhere Treibstoff- und Versicherungskosten, gebundene Kapazität [@imfportwatch2025; @ft2024suez].

![Handelsvolumen durch globale Engpässe (Suez, indexiert). Quelle: IMF PortWatch/HDX.](../images/panama_suez_trade_capacity.svg){#fig:suez width=85%}

Die Straße von Hormus ist einer der wichtigsten maritimen Engpässe, insbesondere für Öl und Gas, aber auch für containerisierten Welthandel. @fig:hormuz zeigt das geschätzte Transitvolumen 2025–2026. In akuten Krisenphasen sinkt der Transit stärker als das globale Handelsvolumen, weil Schiffe die Route meiden oder verzögert fahren, während Güter teils umgeleitet oder aus Lagerbeständen bedient werden [@imfportwatch2025; @reuters2026hormuz].

![Transitvolumen Straße von Hormus (7-Tage-Durchschnitt, Index 2025 = 100). Quelle: IMF PortWatch/HDX.](../images/hormuz_trade_volume_2026.svg){#fig:hormuz width=85%}

Öl ist ein global gehandelter Rohstoff: Risiken an Hormus wirken auf Brent- und WTI-Preise weltweit (@fig:oil-2026). Die Transmission läuft über Energie- und Transportkosten, Inflation, Leistungsbilanzen energieimportierender Länder und politische Reaktionen (Strategische Reserven, Subventionen, geldpolitische Verschärfung) [@fred2025; @reuters2026hormuz].

![Brent- und WTI-Ölpreise während der Iran-/Hormus-Krise 2026. Quelle: EIA via FRED.](../images/oil_prices_iran_2026.svg){#fig:oil-2026 width=85%}

## Klimawandel, Emissionen und die Energiewende

@fig:co2-total zeigt weltweite CO~2~-Emissionen (exklusive Landnutzungsänderung, LULUCF) in Gigatonnen [@wdi2025; @ipcc2023]. Trotz Effizienzgewinnen steigen die Gesamtemissionen langfristig mit Wirtschaftsaktivität und Energieverbrauch; 2020 ist der pandemiebedingte Rückgang sichtbar.

![Weltweite CO~2~-Emissionen (exkl. LULUCF, 1990–2024). Quelle: World Bank WDI/EDGAR.](../images/world_co2_total.svg){#fig:co2-total width=85%}

@fig:co2-intensity unterscheidet Emissionen **pro Kopf** und die **CO~2~-Intensität des BIP** (Emissionen pro Dollar Wertschöpfung in Kaufkraftparitäten). Die Intensität sinkt langsam — Wachstum wird etwas "grüner" pro Dollar —, während die Gesamtemissionen dennoch steigen können, solange die Wirtschaft wächst [@ipcc2023; @dechezlepretre2023].

![CO~2~ pro Kopf und CO~2~-Intensität des BIP. Quelle: World Bank WDI/EDGAR/IEA.](../images/world_co2.svg){#fig:co2-intensity width=85%}

Globalisierung erhöht Emissionen durch Transport und Produktion in globalen Wertschöpfungsketten; gleichzeitig erleichtert sie Technologiediffusion für erneuerbare Energien. Der Klimawandel wirkt zurück auf die Wirtschaft: häufigere Wetterextreme, Belastung von Infrastruktur (z. B. niedrige Wasserstände im Panama-Kanal während El Niño) und regionale Versorgungsrisiken [@ipcc2023].

Die Energiewende ersetzt alte Abhängigkeiten (Kohle, Öl) teilweise durch neue (Lithium, Kobalt, Kupfer, seltene Erden). @fig:commodities zeigt Preisindizes (Basis Juni 2012 = 100) für klassische und kritische Rohstoffe [@imfcommodities2025; @iea2024critical; @usgs2024]. Öl und Kohle bleiben volatil (Ukraine-Krieg); Lithium und seltene Erden schwanken stark und sind geografisch konzentriert — ein erheblicher Anteil der Verarbeitung liegt in China [@iea2024critical].

![Rohstoffpreise: klassische und kritische Mineralien (Index Juni 2012 = 100). Quelle: IMF Primary Commodity Prices.](../images/raw_materials.svg){#fig:commodities width=85%}

## Versorgungssicherheit unter Fragmentierung: Leitfragen

Abschließend verdichten sich mehrere Spannungsfelder, die in der Vorlesung diskutiert werden sollen — ohne Patentlösungen, aber mit klaren Begriffen.

**Effizienz versus Resilienz.** Just-in-time-Lieferketten minimieren Lagerkosten; Resilienz verlangt Redundanz, Lager, mehrere Bezugsquellen oder Reshoring. Teurer werden Güter, Arbeitsplätze und politische Verteilungskonflikte verschieben sich [@baldwin2022; @giovanni2022].

**Handelspolitik.** Zölle und Unsicherheit (@fig:epu-trade) können heimische Industrien schützen, verteuern aber Importe und provozieren Gegenmaßnahmen [@piie2025tariffs; @wto2024]. Friend-shoring reduziert Exposure gegenüber "Rivalen", schafft aber neue Konzentrationsrisiken [@imf2023fragmentation].

**Energie und Engpässe.** Lokale Routenrisiken (Suez, Hormus) haben globale Preis- und Inflationswirkungen (den Abbildungen zu Suez, Hormus und Ölpreisen).

**Klima und Rohstoffe.** Gesamtemissionen können steigen, während das BIP emissionsärmer wird (@fig:co2-total, @fig:co2-intensity). Die Energiewende verschiebt, aber beseitigt nicht Rohstoffabhängigkeit (@fig:commodities).

**Rolle von Handel und Finanzmärkten.** Mehr Diversifikation und Partnerländer versus weniger Handel und Eigenversorgung; Finanzmärkte als Versicherungs- und Risikoteilungsmechanismus (Derivate, Cat Bonds) oder als Verstärker von Prozyklizität [@krugman2018; @eichengreen2008].

Globalisierung bleibt ein Entwicklungsmotor; gleichzeitig erfordern Rivalität (z. B. USA–China), Klimaschutz und Versorgungssicherheit eine Neuabwägung zwischen Kooperation und strategischer Autonomie [@rodrik2011; @imf2023fragmentation].

# Anhang: Leistungsnachweis

Studierende verfassen ein Essay von 1000 bis 1200 Wörtern (Einzelarbeit, keine Plagiate, Quellenangaben insbesondere bei Daten). Wissenschaftliche Zeitschriften sind erwünscht; Zeitungs- und Policy-Quellen sind für aktuelle Themen ausdrücklich zulässig. Abgabe bis 14.07.2026 über Moodle.

Themenvorschläge knüpfen an die Vorlesung an: US-Zölle seit 2025; Lieferketten nach COVID-19; Friend-shoring; Suez, Hormus und Energiemärkte; Klimawandel und CO~2~-Entkopplung; Energiewende und Rohstoffe; Thailand 1997; der Ressourcenfluch [@sachs1995resource]. Eigene Themen sind nach Rücksprache möglich.
