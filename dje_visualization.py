"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import dje_constants as C

JOB_COLORS = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#b279a2", "#9d755d", "#72b7b2", "#eeca3b"]


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def zeilen_nach_maschine(M):
    """Operationen nach Maschine und Nummer geordnet (die Zeilen der Fenster-Abbildung)."""
    return [o for ops in M.maschinen_ops for o in ops]


def build_fenster(M, est, lst, H):
    """Fenster je Operation, geordnet nach Maschine: hell das Fenster [est, lct], dunkel der Pflichtteil [lst, est + d); rote Linie: Horizont H."""
    ops = zeilen_nach_maschine(M)
    labels = [f"M{M.maschine[o]} · {M.bezeichnung(o)} d={M.d[o]}" for o in ops]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        orientation="h", y=labels, x=[lst[o] + M.d[o] - est[o] for o in ops], base=[est[o] for o in ops], marker=dict(color=C.COLOR_WINDOW, line=dict(color=C.COLOR_WINDOW_LINE, width=1)),
        name="Fenster (est bis lct)", customdata=[[est[o], lst[o]] for o in ops], hovertemplate="%{y}: est %{customdata[0]}, lst %{customdata[1]}<extra></extra>"))
    pflicht = [o for o in ops if lst[o] < est[o] + M.d[o]]
    fig.add_trace(go.Bar(
        orientation="h", y=[f"M{M.maschine[o]} · {M.bezeichnung(o)} d={M.d[o]}" for o in pflicht], x=[est[o] + M.d[o] - lst[o] for o in pflicht], base=[lst[o] for o in pflicht],
        marker=dict(color=C.COLOR_MANDATORY), name="Pflichtteil (lst bis est + d)", hovertemplate="%{y}: Pflichtteil von %{base} bis %{x}<extra></extra>"))
    fig.add_vline(x=H, line=dict(color=C.COLOR_HORIZON, width=2, dash="dash"), annotation_text=f"H = {H}", annotation_position="top")
    fig.update_layout(barmode="overlay", bargap=0.25)
    fig.update_xaxes(title_text="Zeit", range=[0, H + 1], dtick=1)
    fig.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=labels)
    return _base(fig, height=max(260, 34 * len(ops) + 90))


def build_gantt(M, starts):
    """Plan als Balkendiagramm: eine Zeile je Maschine, Farbe je Auftrag, Beschriftung (j,k)."""
    fig = go.Figure()
    gezeigt = set()
    for o in range(M.n):
        j = M.name[o][0]
        fig.add_trace(go.Bar(
            orientation="h", y=[f"Maschine {M.maschine[o]}"], x=[M.d[o]], base=[starts[o]], marker=dict(color=JOB_COLORS[j % len(JOB_COLORS)], line=dict(color="white", width=1)),
            name=f"Auftrag {j}", legendgroup=f"j{j}", showlegend=j not in gezeigt, text=[M.bezeichnung(o)], textposition="inside", insidetextanchor="middle",
            hovertemplate=f"{M.bezeichnung(o)}: Start {starts[o]}, Dauer {M.d[o]}<extra></extra>"))
        gezeigt.add(j)
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title_text="Zeit", dtick=5)
    fig.update_yaxes(autorange="reversed", categoryorder="array", categoryarray=[f"Maschine {m}" for m in range(M.n_maschinen)])
    return _base(fig, height=max(240, 52 * M.n_maschinen + 100))


def build_verteilung(werte_je_stufe: dict, abbrueche_je_stufe: dict, budget: int, titel_y="Knoten bis zum bewiesenen Optimum"):
    """Verteilung der Knotenzahlen je Stufe (logarithmische Achse): Kasten mit allen Punkten; rote Kreuze: Abbruch am Budget (untere Schranke)."""
    fig = go.Figure()
    for stufe, werte in werte_je_stufe.items():
        name = C.STAGE_SHORT[stufe]
        fig.add_trace(go.Box(y=werte, name=name, boxpoints="all", jitter=0.45, pointpos=0, marker=dict(color=C.COLOR_STAGE[stufe], size=6), line=dict(color=C.COLOR_STAGE[stufe]),
                             hovertemplate="%{y} Knoten<extra></extra>", showlegend=False))
        n_ab = abbrueche_je_stufe.get(stufe, 0)
        if n_ab:
            fig.add_trace(go.Scatter(x=[name] * 1, y=[budget], mode="markers+text", marker=dict(color=C.COLOR_HORIZON, symbol="x", size=11), text=[f"{n_ab} Abbruch"], textposition="top center",
                                     name="Abbruch am Budget", showlegend=False, hovertemplate=f"{n_ab} Abbrüche am Budget {budget}<extra></extra>"))
    fig.update_yaxes(type="log", title_text=titel_y)
    return _base(fig, height=380)


def build_ursachen(zeilen):
    """Fehlschläge nach Ursache je Stufe (Summe über die Instanzen), gestapelt. `zeilen`: [{stufe, vorrang, paar, edge}]."""
    fig = go.Figure()
    namen = [C.STAGE_SHORT[z["stufe"]] for z in zeilen]
    for key, text, farbe in (("vorrang", "durch Vorrang (leeres Fenster)", "#9a9a9a"), ("paar", "durch Paar-Test", "#4c78a8"), ("edge", "durch Edge-Finding", "#2F6B65")):
        fig.add_trace(go.Bar(x=namen, y=[z[key] for z in zeilen], name=text, marker_color=farbe))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Fehlschläge (Summe über die Instanzen)")
    return _base(fig, height=340)
