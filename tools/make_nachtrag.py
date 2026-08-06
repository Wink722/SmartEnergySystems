"""Builds the supplement PDF that closes the gaps in the three Kompendien."""
import fitz

OUT = (r"C:\Users\vince\Desktop\Studium\smart Energy Systems"
       r"\Claude Zusammenfassungen\Nachtrag Fehlende Themen.pdf")

CSS = """
* { font-family: sans-serif; }
body { font-size: 9.5pt; line-height: 1.45; color: #16181C; }
h1 { font-size: 25pt; color: #3F6B52; margin-bottom: 2pt; line-height:1.1; }
h2 { font-size: 14pt; color: #3F6B52; margin-top: 16pt; margin-bottom: 3pt; }
h3 { font-size: 10.5pt; color: #16181C; margin-top: 10pt; margin-bottom: 2pt; }
p  { margin-top: 0pt; margin-bottom: 6pt; }
.lead { font-size: 11pt; color: #444; margin-bottom: 10pt; }
.eyebrow { font-size: 7.5pt; color: #6E7178; letter-spacing: 1pt; margin-bottom: 12pt; }
.tag { font-size: 8pt; color: #9A6216; margin-bottom: 4pt; }
.box { background-color: #E4EDE6; padding: 7pt; margin-bottom: 8pt; }
.warn { background-color: #F7EEDF; padding: 7pt; margin-bottom: 8pt; }
.small { font-size: 8.5pt; color: #6E7178; }
table { font-size: 8pt; border: 1px solid #D8D1C6; }
th { background-color: #3F6B52; color: #FFFFFF; padding: 3pt; text-align: left; font-size: 8pt; }
td { padding: 3pt; border-bottom: 1px solid #E5DFD6; vertical-align: top; }
td.k { background-color: #F2EEE8; }
ul { margin-top: 0pt; margin-bottom: 6pt; }
li { margin-bottom: 2pt; }
"""

HTML = """
<div class="eyebrow">NACHTRAG ZU DEN DREI KOMPENDIEN &middot; SMART ENERGY INFRASTRUCTURE &middot; KIT WiSe 2025/26</div>
<h1>Was in den Zusammenfassungen fehlt</h1>
<p class="lead">Gepr&uuml;ft wurden rund 90 Themen aus allen 642 Inhaltsfolien gegen die drei
Kompendien &mdash; erst auf Erw&auml;hnung, dann auf Tiefe, dann gezielt auf das, was laut
Ged&auml;chtnisprotokoll wirklich abgefragt wurde.</p>
<div class="box"><b>Befund:</b> Die Abdeckung ist gut. Fast alle Themen sind vorhanden, und die
Rechenteile sind stark &mdash; spezifische Beschaffungskosten, Speicherkostenformel, Merit-Order,
Convolution, alle f&uuml;nf Entscheidungsregeln, Haber-Bosch, Methanol-Route. Es fehlen f&uuml;nf
Dinge. Zwei davon sind klausurrelevant, weil sie in fr&uuml;heren Klausuren gefragt wurden.</p>
<p class="small">Dieses Dokument liefert das Fehlende &mdash; es listet die L&uuml;cken nicht nur auf.</p></div>

<h2>1 &middot; LNG-Wertsch&ouml;pfungskette: die Kostenanteile</h2>
<p class="tag">KLAUSURRELEVANT &middot; WS 25/26 wurde genau danach gefragt &middot; Folie 145</p>
<p>Die Kompendien beschreiben die f&uuml;nfstufige Kette und sagen richtig, dass die
Verfl&uuml;ssigung der teuerste Schritt ist. Die <b>Prozentzahlen fehlen</b> &mdash; und die
Klausurfrage lautete: &bdquo;Wertsch&ouml;pfungskette zeichnen und sagen, welche Schritte die
h&ouml;chsten Kosten verursachen.&ldquo;</p>
<table>
<tr><th>Stufe</th><th>Was passiert</th><th>Kostenanteil</th></tr>
<tr><td class="k">1 &middot; Exploration &amp; Produktion</td><td>Feld finden, f&ouml;rdern, aufbereiten</td><td>11 %</td></tr>
<tr><td class="k">2 &middot; Verfl&uuml;ssigung</td><td>CO2, Wasser, H2S abtrennen, auf &minus;162 &deg;C k&uuml;hlen, Volumen &divide; 600</td><td><b>42 %</b></td></tr>
<tr><td class="k">3 &middot; Transport</td><td>Verschiffung im LNG-Tanker (Moss-Kugel oder Membran), Boil-off als Treibstoff</td><td>20 %</td></tr>
<tr><td class="k">4 &middot; Speicherung &amp; Regasifizierung</td><td>Importterminal: Tanks, Verdampfer, Einspeisung ins Netz</td><td><b>27 %</b></td></tr>
<tr><td class="k">5 &middot; Kunde</td><td>&mdash;</td><td>&mdash;</td></tr>
</table>
<div class="box"><b>Der Merksatz f&uuml;r die Klausur:</b> Verfl&uuml;ssigung 42 %, Regasifizierung
27 % &mdash; die beiden teuersten Schritte sitzen an den <i>Enden</i> der Kette und wachsen
<i>nicht</i> mit der Distanz. Genau deshalb schl&auml;gt LNG die Pipeline ab einer bestimmten
Entfernung: die Seestrecke selbst kostet nur 20 %.</div>

<h2>2 &middot; Die Vergleichstabelle der H<sub>2</sub>-Derivate</h2>
<p class="tag">KLAUSURRELEVANT &middot; WS 25/26 als Ankreuztabelle gefragt &middot; Folie 706</p>
<p>Die Derivate werden in Block 3 &uuml;ber die Kapitel verteilt verglichen, aber
<b>die Tabelle als Tabelle fehlt</b>: keine Zeile Pipeline-Kompatibilit&auml;t, keine
Schiffsgr&ouml;&szlig;en in dwt. Die Klausurfrage war: welche der Stoffe lassen sich in welchen
Transport- und Speicheroptionen wiederverwenden?</p>
<h3>Wasserstoff, Ammoniak, Methanol</h3>
<table>
<tr><th></th><th>Wasserstoff</th><th>Ammoniak</th><th>Methanol</th></tr>
<tr><td class="k">Sicherheit</td><td>hoch entz&uuml;ndlich</td><td>korrosiv, (&ouml;ko-)toxisch, &auml;tzend, Eutrophierungsrisiko, NOx &amp; N2O</td><td>toxisch f&uuml;r Menschen, nicht f&uuml;r Wasserfauna, hoch entz&uuml;ndlich</td></tr>
<tr><td class="k">Speicherung</td><td>gek&uuml;hlte oder Hochdrucktanks n&ouml;tig</td><td>gek&uuml;hlte oder Drucktanks n&ouml;tig</td><td><b>hohe Kompatibilit&auml;t</b></td></tr>
<tr><td class="k">Schiffstransport</td><td><b>keine Wiederverwendung</b>, nur 1 Prototyp mit 2.200 dwt</td><td>etabliert, Schiffe bis 75.000 dwt</td><td>etabliert, m&ouml;gliche Wiederverwendung von &Ouml;ltankern</td></tr>
<tr><td class="k">Pipeline</td><td>Umr&uuml;stkosten 10&ndash;35 % eines Neubaus</td><td><b>keine Wiederverwendung</b></td><td>Kompatibilit&auml;t unklar</td></tr>
</table>
<h3>LOHC, Methan (SNG), Fischer-Tropsch-Kraftstoffe</h3>
<table>
<tr><th></th><th>LOHC</th><th>Methan</th><th>FT-Kraftstoffe</th></tr>
<tr><td class="k">Sicherheit</td><td>abh&auml;ngig vom Tr&auml;germaterial</td><td>starkes Treibhausgas</td><td>toxisch</td></tr>
<tr><td class="k">Speicherung</td><td>hohe Kompatibilit&auml;t</td><td>gek&uuml;hlte oder Hochdrucktanks n&ouml;tig</td><td>hohe Kompatibilit&auml;t</td></tr>
<tr><td class="k">Schiffstransport</td><td>m&ouml;gliche Wiederverwendung von &Ouml;ltankern &gt; 500.000 dwt</td><td>etabliert, Schiffe bis 120.000 dwt</td><td>m&ouml;gliche Wiederverwendung von &Ouml;ltankern &gt; 500.000 dwt</td></tr>
<tr><td class="k">Pipeline</td><td>hohe Kompatibilit&auml;t</td><td>hohe Kompatibilit&auml;t</td><td>hohe Kompatibilit&auml;t</td></tr>
</table>
<div class="box"><b>Das Muster in einem Satz:</b> Je mehr sich ein Molek&uuml;l wie ein Brennstoff
verh&auml;lt, den wir heute schon verschiffen, desto mehr Infrastruktur erbt es. Methanol und
FT-Kraftstoffe erben die &Ouml;lwelt, SNG die komplette Erdgaswelt, Ammoniak die LPG- und
D&uuml;ngemittelwelt &mdash; und reiner Wasserstoff erbt fast nichts.</div>
<p class="small"><b>Untergrundspeicher</b> (in der Tabelle nicht enthalten, aber mitgefragt):
Wasserstoff in Salzkavernen erprobt, Porenspeicher unklar wegen mikrobieller Aktivit&auml;t.
Methan in allen Speichertypen etabliert. Ammoniak und Methanol werden nicht untertage
gespeichert, sondern in Tanks &mdash; sie sind bei Umgebungsbedingungen fl&uuml;ssig genug.</p>

<h2>3 &middot; Gasqualit&auml;t: H-Gas und L-Gas im Detail</h2>
<p class="tag">MITTLERES RISIKO &middot; Folien 100 und 101</p>
<p>Wobbe-Index, Brenn- und Heizwert sowie die Normbedingungen stehen in Block 1. Was fehlt,
sind die <b>Zusammensetzungen</b> &mdash; und die braucht man, um zu erkl&auml;ren, <i>warum</i>
zwei Gase nicht austauschbar sind.</p>
<table>
<tr><th>Komponente</th><th>Russ. H-Gas</th><th>Nordsee H-Gas</th><th>D&auml;n. H-Gas</th><th>Niederl. L-Gas</th><th>Dt. L-Gas</th></tr>
<tr><td class="k">Methan CH4</td><td>96,96</td><td>88,71</td><td>90,07</td><td>83,64</td><td>86,46</td></tr>
<tr><td class="k">Stickstoff N2</td><td>0,86</td><td>0,82</td><td>0,28</td><td><b>10,21</b></td><td><b>10,24</b></td></tr>
<tr><td class="k">Kohlendioxid CO2</td><td>0,18</td><td>1,94</td><td>0,60</td><td>1,68</td><td>2,08</td></tr>
<tr><td class="k">Ethan C2H6</td><td>1,37</td><td>6,93</td><td>5,68</td><td>3,56</td><td>1,06</td></tr>
<tr><td class="k">Propan C3H8</td><td>0,45</td><td>1,25</td><td>2,19</td><td>0,61</td><td>0,11</td></tr>
<tr><td class="k">Butane C4H10</td><td>0,15</td><td>0,28</td><td>0,90</td><td>0,19</td><td>0,03</td></tr>
<tr><td class="k">Schwefel gesamt</td><td colspan="5">alle Sorten &lt; 3 bis &lt; 5 mg/m&sup3;</td></tr>
</table>
<p class="small">Angaben in mol%. Grobfassung von Folie 100: L-Gas ca. 85 % Methan, 4 % h&ouml;here
Alkane, 11 % Inertgase &middot; H-Gas Nordsee ca. 89 / 8 / 3 &middot; H-Gas GUS ca. 98 / 1 / 1.</p>
<div class="warn"><b>Widerspruch im Material:</b> Folie 100 rundet das GUS-H-Gas auf
&bdquo;ca. 98 % Methan&ldquo;, die Tabelle auf Folie 101 nennt 96,96 mol% f&uuml;r russisches
H-Gas. Nimm die Tabellenwerte, wenn gerechnet werden soll.</div>
<p><b>Warum der Unterschied z&auml;hlt:</b> L-Gas tr&auml;gt rund 10 % Stickstoff als
Inertgas mit. Der senkt den Brennwert und damit den Wobbe-Index, weshalb ein L-Gas-Brenner
nicht ohne Umstellung mit H-Gas l&auml;uft &mdash; das ist der technische Kern der
Marktraumumstellung.</p>

<h2>4 &middot; &Ouml;l: Bevorratung und Frachtraten</h2>
<p class="tag">GERINGES RISIKO &middot; Folien 313 und 317</p>
<h3>Erd&ouml;lbevorratung (ErdölBevG)</h3>
<p>Der Erd&ouml;lbevorratungsverband (EBV), gegr&uuml;ndet 1978, ist eine K&ouml;rperschaft des
&ouml;ffentlichen Rechts mit Sitz in Hamburg. Er h&auml;lt vom 1. April bis 31. M&auml;rz
st&auml;ndig Vorr&auml;te in H&ouml;he der <b>t&auml;glichen durchschnittlichen Nettoeinfuhren
f&uuml;r 90 Tage</b>, bezogen auf die letzten drei Kalenderjahre vor dem Bevorratungszeitraum.
Alle Unternehmen, die die betroffenen Produkte herstellen oder importieren, sind
Pflichtmitglieder und zahlen Beitr&auml;ge (Gr&ouml;&szlig;enordnung 3,56 &euro;/t).</p>
<p class="small"><b>Merke:</b> Bezugsgr&ouml;&szlig;e ist die <i>Nettoeinfuhr</i> der Vorjahre,
nicht der Verbrauch und nicht die Produktion. Die Parallele zur Gasspeicher-Regulierung ist
gewollt: In beiden F&auml;llen &uuml;berschreibt der Staat das kommerzielle Optimum zugunsten
der Versorgungssicherheit.</p>
<h3>Frachtratensystem AFRA</h3>
<p>Schiffschartervertr&auml;ge verweisen meist auf das <b>AFRA</b>-System (Average Freight Rate
Assessment), das Tankergr&ouml;&szlig;en klassifiziert &mdash; Aframax, Suezmax, VLCC, ULCC &mdash;
und standardisierte Frachtraten setzt. Dazu die operativen Klauseln: Schiffsspezifikation,
Lade- und L&ouml;schh&auml;fen, <b>Laytime</b> (erlaubte Lade-/L&ouml;schzeit),
<b>Demurrage</b> (Strafe bei &Uuml;berschreitung) sowie Versicherung und Haftung
f&uuml;r Verschmutzung, Ladungsverlust und Unf&auml;lle.</p>
<p><b>Raffineriemarge</b> ist die Differenz zwischen dem Wert des Produktkorbs und dem
Rohölpreis. Sie erkl&auml;rt, warum Produktpreise und Rohölpreis auseinanderlaufen: steigt die
Marge, verdient die Raffinerie an der Verarbeitung, unabh&auml;ngig vom absoluten &Ouml;lpreis.</p>

<h2>5 &middot; Energieeinheiten und dekadische Pr&auml;fixe</h2>
<p class="tag">GRUNDLAGE &middot; Folien 15 bis 17</p>
<p>In keinem Kompendium enthalten. Jede Gasaufgabe beginnt mit einer Umrechnung, deshalb hier
die Zeilen, die man wirklich braucht.</p>
<table>
<tr><th>Von &rarr; nach</th><th>Faktor</th></tr>
<tr><td class="k">1 kWh &rarr; Joule</td><td>3,6 &middot; 10<sup>6</sup> J = 3,6 MJ</td></tr>
<tr><td class="k">1 Joule &rarr; kWh</td><td>2,7778 &middot; 10<sup>&minus;7</sup></td></tr>
<tr><td class="k">1 Btu &rarr; kWh</td><td>2,9307 &middot; 10<sup>&minus;4</sup></td></tr>
<tr><td class="k">1 t SKE (Steinkohleeinheit) &rarr; kWh</td><td>8.141</td></tr>
<tr><td class="k">1 t &Ouml;l&auml;quivalent (toe) &rarr; kWh</td><td>11.630</td></tr>
<tr><td class="k">1 m&sup3; &rarr; Liter</td><td>1.000</td></tr>
<tr><td class="k">1 bbl (US-Barrel) &rarr; Liter</td><td>158,99 (= 42 US-Gallonen)</td></tr>
<tr><td class="k">1 m&sup3; &rarr; bbl</td><td>6,2898</td></tr>
<tr><td class="k">1 cft (Kubikfu&szlig;) &rarr; m&sup3;</td><td>0,02831685</td></tr>
</table>
<p><b>Pr&auml;fixe:</b> Kilo k = 10<sup>3</sup> &middot; Mega M = 10<sup>6</sup> &middot;
Giga G = 10<sup>9</sup> &middot; Tera T = 10<sup>12</sup> &middot; Peta P = 10<sup>15</sup> &middot;
Exa E = 10<sup>18</sup>. Nach unten: Milli m = 10<sup>&minus;3</sup> &middot;
Mikro &micro; = 10<sup>&minus;6</sup> &middot; Nano n = 10<sup>&minus;9</sup>.</p>
<div class="box"><b>Die Umrechnung, die in jeder Gasaufgabe steht:</b><br/>
&kappa;<sub>E</sub> = &kappa;<sub>V</sub> &middot; Brennwert &nbsp;&rarr;&nbsp;
10.000 m&sup3;/h &middot; 11 kWh/m&sup3; = 110.000 kWh/h = 110.000 kW = 110 MW.<br/>
Und: &euro;/(kWh/h)/a ist dasselbe wie &euro;/kW/a &mdash; ein Leistungspreis, kein Energiepreis.</div>
<p>&nbsp;</p>

<h2>6 &middot; Was ich verd&auml;chtigt hatte, was aber drin ist</h2>
<p>Damit du nichts doppelt lernst: Diese Themen wirkten bei der ersten Stichwortsuche wie
L&uuml;cken, sind aber vorhanden &mdash; die Kompendien benutzen nur andere W&ouml;rter.</p>
<ul>
<li><b>Vier Ebenen der Netzindustrie</b> &mdash; als &bdquo;Netzdienste / Infrastrukturmanagement /
Netzinfrastrukturen / &ouml;ffentliche Ressourcen&ldquo; vollst&auml;ndig in Block 1.</li>
<li><b>Planungsaufgaben der Versorger</b> &mdash; mit allen K&auml;sten: Kurzfrist &lt; 1 a
(Day-Ahead, Unit Commitment, Intraday, Echtzeitbilanz), Mittelfrist 1&ndash;5 a
(Portfolio-Optimierung, Hedging, Wartungsplanung), Langfrist &gt; 5 a (Investition, Ausbau,
Stilllegung), dazu deterministisch &rarr; stochastisch &rarr; Szenarien.</li>
<li><b>Perfect Foresight vs. Time-Step</b> &mdash; kompakt, aber mit Vor- und Nachteil je Ansatz.</li>
<li><b>Merit-Order</b> &mdash; mit dem Rechenbeispiel 50,35 &euro;/MWh<sub>el</sub>.</li>
<li><b>Normbedingungen</b> 1,01325 bar und 273,15 K.</li>
<li><b>Elektrolyseurkapazit&auml;t</b> 2 GW Ende 2024, ca. 5.000 GW n&ouml;tig bis 2050.</li>
</ul>

<h2>7 &middot; Fehler in den Folien, die in den Kompendien nicht markiert sind</h2>
<p>Beim Aufbau des Fragenkatalogs sind 47 Fehler und Widerspr&uuml;che in den Folien
aufgefallen. Diese sechs k&ouml;nnen in der Klausur Punkte kosten:</p>
<ul>
<li><b>Folie 567, Regelleistung:</b> Das zweite Band ist ein zweites Mal mit &bdquo;Primary
control&ldquo; beschriftet; die deutsche Textebene darunter sagt &bdquo;Sekund&auml;rregelung&ldquo;.
Lies das Diagramm &uuml;ber die Zeitachse: 5 s / 30 s / 15 min / 1 h &rarr; Prim&auml;r-,
Sekund&auml;r-, Terti&auml;rregelung, Stundenreserve. &Uuml;NB bis 1 h, danach der Bilanzkreis.</li>
<li><b>Folie 643, Ammoniak:</b> &bdquo;45 % des weltweiten Wasserstoffbedarfs&ldquo; passt nicht
zu den eigenen Zahlen: 150 Mt/a NH3 &middot; 0,18 kg H2/kg = 27 Mt, also rund 25 % von 110 Mt.</li>
<li><b>Wasserstoff-Weltproduktion:</b> 100, 110 und 120 Mt/a auf drei verschiedenen Folien.
Nimm 110 Mt/a und nenne die Folie.</li>
<li><b>H2-&Uuml;bungsl&ouml;sung:</b> &bdquo;1.000 MWh_el&ldquo; muss kWh_el sein, sonst kommen die
100,95 kg NH3 nicht heraus. Und &bdquo;8,94 kg / l&ldquo; meint 8,94 kg Wasser je kg Wasserstoff.</li>
<li><b>Folie 497, Investitionsrechnung:</b> setzt &bdquo;required rate of return&ldquo; mit dem
IRR gleich &mdash; das eine ist eine Vorgabe des Investors, das andere ein Ergebnis des Projekts.
Bei mehreren Vorzeichenwechseln ist der IRR schlicht nicht aussagekr&auml;ftig; entschieden wird
&uuml;ber den Kapitalwert.</li>
<li><b>Folien 661 und 663, Methanol:</b> Reaktionsenthalpie (&minus;91,8 kJ/mol) und
Crack-Bedingungen (50&ndash;100 bar, 600&ndash;900 &deg;C) sind aus den Ammoniak-Folien kopiert.
Methanol-Reformierung l&auml;uft bei etwa 250&ndash;350 &deg;C &mdash; und genau diese Milde ist
einer der echten Vorteile von Methanol.</li>
</ul>

<p class="small" style="margin-top:14pt">Erstellt beim Aufbau der Lern-App zu Smart Energy
Infrastructure. Alle genannten Folienzahlen beziehen sich auf das zusammengef&uuml;hrte Skript
(736 Seiten) im Repository <b>Wink722/SmartEnergySystems</b>, in dem jede Aussage als Frage mit
Musterl&ouml;sung hinterlegt ist.</p>
"""


def main() -> None:
    mediabox = fitz.paper_rect("a4")
    where = mediabox + (56, 52, -56, -56)

    writer = fitz.DocumentWriter(OUT)
    story = fitz.Story(HTML, user_css=CSS)
    more, n = 1, 0
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
        n += 1
        if n > 40:
            break
    writer.close()

    # page numbers, added in a second pass
    doc = fitz.open(OUT)
    for i, page in enumerate(doc):
        page.insert_text((56, 812), f"Nachtrag · Fehlende Themen", fontsize=7,
                         color=(0.62, 0.62, 0.62))
        page.insert_text((520, 812), f"{i + 1} / {doc.page_count}", fontsize=7,
                         color=(0.62, 0.62, 0.62))
    doc.set_metadata({"title": "Nachtrag – Was in den Kompendien fehlt",
                      "author": "Smart Energy Infrastructure, KIT WiSe 2025/26"})
    doc.save(OUT, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    pages = doc.page_count
    doc.close()
    print(f"{pages} Seiten -> {OUT}")


if __name__ == "__main__":
    main()
