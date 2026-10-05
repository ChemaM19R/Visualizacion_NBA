import ast
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, State, ctx, no_update



# 1. DATOS
# ============================================================================================================================================================================================================
df = pd.read_csv("dataframe_nba.csv")
df["season"] = df["season"].astype(int)

sin_pm = df.groupby("season")["plusMinusPoints"].transform(lambda s: (s == 0).all())
df.loc[sin_pm, "plusMinusPoints"] = np.nan

df["equipos"] = df["teams"].str.strip("[]").str.replace("'", "", regex=False)

MIN_PARTIDOS = 10  #no inflar graficos o estadisticas con outliers

TEMPORADAS = sorted(int(t) for t in df["season"].unique())
T_MIN, T_MAX = TEMPORADAS[0], TEMPORADAS[-1]



# 2. DICCIONARIOS PARA EL MAPA (tu código)
# ============================================================================================================================================================================================================
ESTADOS_COD = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Washington D.C.": "DC", "Florida": "FL", "Georgia": "GA", "Hawái": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Luisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Misisipi": "MS", "Misuri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "Nuevo Hampshire": "NH", "Nueva Jersey": "NJ", "Nuevo México": "NM",
    "Nueva York": "NY", "Carolina del Norte": "NC", "Dakota del Norte": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pensilvania": "PA", "Rhode Island": "RI",
    "Carolina del Sur": "SC", "Dakota del Sur": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "Virginia Occidental": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

PAISES_COD = {
    "España": "ESP", "Francia": "FRA", "Italia": "ITA", "Turquía": "TUR",
    "Serbia": "SRB", "Australia": "AUS", "Grecia": "GRC", "Alemania": "DEU",
    "Rusia": "RUS", "China": "CHN", "Lituania": "LTU", "Eslovenia": "SVN",
    "Brasil": "BRA", "Ucrania": "UKR", "Croacia": "HRV", "Israel": "ISR",
    "Montenegro": "MNE", "Canadá": "CAN", "Bélgica": "BEL", "Hungría": "HUN",
    "Argentina": "ARG", "Letonia": "LVA", "Nueva Zelanda": "NZL", "Japón": "JPN",
    "Uruguay": "URY", "Polonia": "POL", "Venezuela": "VEN", "Cuba": "CUB",
    "Puerto Rico": "PRI", "Irán": "IRN", "Bulgaria": "BGR", "Corea del Sur": "KOR",
    "Bosnia y Herzegovina": "BIH", "Macedonia del Norte": "MKD", "República Checa": "CZE",
    "Georgia (país)": "GEO", "Nigeria": "NGA", "Senegal": "SEN", "Camerún": "CMR",
    "Congo": "COD", "Sudán del Sur": "SSD", "México": "MEX", "República Dominicana": "DOM",
    "Bahamas": "BHS", "Jamaica": "JAM", "Panamá": "PAN", "Reino Unido": "GBR",
    "Suiza": "CHE", "Austria": "AUT", "Suecia": "SWE", "Finlandia": "FIN",
    "Dinamarca": "DNK", "Países Bajos": "NLD", "Portugal": "PRT",
    "Estonia": "EST", "Rumanía": "ROU", "Egipto": "EGY", "Túnez": "TUN",
    "Filipinas": "PHL", "India": "IND", "Mali": "MLI", "Guinea": "GIN",
}

TRADUCCION = {
    "France": "Francia", "Brazil": "Brasil", "Greece": "Grecia", "Canada": "Canadá",
    "Spain": "España", "Italy": "Italia", "Germany": "Alemania", "Turkey": "Turquía",
    "Russia": "Rusia", "Lithuania": "Lituania", "Slovenia": "Eslovenia", "Ukraine": "Ucrania",
    "Croatia": "Croacia", "Belgium": "Bélgica", "Hungary": "Hungría", "Latvia": "Letonia",
    "New Zealand": "Nueva Zelanda", "Japan": "Japón", "Poland": "Polonia", "Iran": "Irán",
    "South Korea": "Corea del Sur", "Bosnia and Herzegovina": "Bosnia y Herzegovina",
    "North Macedonia": "Macedonia del Norte", "Czech Republic": "República Checa",
    "Cameroon": "Camerún", "DRC": "Congo", "Democratic Republic of the Congo": "Congo",
    "South Sudan": "Sudán del Sur", "Mexico": "México", "Dominican Republic": "República Dominicana",
    "Panama": "Panamá", "United Kingdom": "Reino Unido", "England": "Reino Unido",
    "Great Britain": "Reino Unido", "Switzerland": "Suiza", "Sweden": "Suecia",
    "Finland": "Finlandia", "Denmark": "Dinamarca", "Netherlands": "Países Bajos",
    "Romania": "Rumanía", "Egypt": "Egipto", "Tunisia": "Túnez", "Philippines": "Filipinas",
}


df["formacion"] = df["formacion"].astype(str).str.strip().replace(TRADUCCION)
df["cod_estado"] = df["formacion"].map(ESTADOS_COD)
df["cod_pais"] = df["formacion"].map(PAISES_COD)

# lista de equipos por jugador
df["lista_equipos"] = df["teams"].apply(ast.literal_eval)
OPCIONES_EQUIPO = sorted(df["lista_equipos"].explode().dropna().unique())
EQUIPOS_POR_TEMPORADA = (df[["season", "lista_equipos"]].explode("lista_equipos").dropna()
                         .groupby("season")["lista_equipos"].apply(lambda s: sorted(s.unique())).to_dict())

# identificar jugadores para el filtro(nombre y temporadas jugadas)
_carreras = (df.groupby("personId")
               .agg(nombre=("fullName", "first"), desde=("season", "min"), hasta=("season", "max"))
               .sort_values("nombre"))
OPCIONES_JUGADOR = [
    {"label": f"{r.nombre} ({r.desde}–{r.hasta})" if r.desde != r.hasta else f"{r.nombre} ({r.desde})",
     "value": int(pid)}
    for pid, r in _carreras.iterrows()
]
NOMBRE_JUGADOR = _carreras["nombre"].to_dict()

# escala fija de colores en el mapa
en_mapa = df["cod_estado"].notna() | df["cod_pais"].notna()
MAX_JUG = df[en_mapa].groupby(["season", "formacion"]).size().max()
TICKS = [t for t in [1, 2, 5, 10, 25, 50, 100] if t <= MAX_JUG]



# 3. ESTILO
# ============================================================================================================================================================================================================
# colores eeleccionados inspirados en baloncesto y pabellón
TINTA = "#14213D"      
BALON = "#E4572E"      
MADERA = "#C8924F"     
FONDO = "#ECEEF1"      
PANEL = "#FFFFFF"
LINEA = "#D9DCE1"
SUAVE = "#5F6B7A"
ORO = "#F2B705"        
FUENTE_TITULOS = "'Barlow Condensed', 'Arial Narrow', 'Roboto Condensed', sans-serif"
FUENTE_TEXTO = "'Barlow', 'Segoe UI', Helvetica, Arial, sans-serif"

COLOR_TEXTO = TINTA
COLOR_SUAVE = SUAVE

# Negro (negativo) -> gris claro (0) -> oro (positivo)
ESCALA_PM = [[0.0, "#000000"], [0.5, "#E1E3E6"], [1.0, ORO]]
# Mapa: de parquet claro a naranja balón y marrón tostado
ESCALA_MAPA = [[0.0, "#F7E6D8"], [0.35, "#EFA47C"], [0.7, BALON], [1.0, "#7A230C"]]

# Plantilla común para todos los gráficos de Plotly
pio.templates["nba"] = go.layout.Template(layout=dict(
    font=dict(family=FUENTE_TEXTO, color=TINTA, size=13),
    title=dict(font=dict(family=FUENTE_TITULOS, size=23, color=TINTA), x=0, xref="paper",
               xanchor="left", y=0.97, yanchor="top"),
    paper_bgcolor=PANEL, plot_bgcolor=PANEL,
    xaxis=dict(gridcolor="#EEF0F3", linecolor=LINEA, zeroline=False, ticks="",
               title=dict(font=dict(color=SUAVE, size=13))),
    yaxis=dict(gridcolor="#EEF0F3", linecolor=LINEA, zeroline=False, ticks="",
               title=dict(font=dict(color=SUAVE, size=13))),
    hoverlabel=dict(bgcolor=TINTA, bordercolor=TINTA,
                    font=dict(family=FUENTE_TEXTO, color="white", size=13)),
    colorway=[TINTA, BALON, MADERA],
))
pio.templates.default = "plotly_white+nba"


def subtitulo_grafico(texto):
    return (f"<br><span style='font-family:Barlow, sans-serif;font-size:13px;"
            f"color:{SUAVE}'>{texto}</span>")


KPIS = [
    ("points", "Puntos por partido"),
    ("assists", "Asistencias por partido"),
    ("reboundsTotal", "Rebotes por partido"),
    ("numMinutes", "Minutos por partido"),
]


# Filtros por media por partido: (columna, etiqueta, paso del slider)
FILTROS = [
    ("points", "Puntos", 0.5),
    ("assists", "Asistencias", 0.5),
    ("reboundsTotal", "Rebotes", 0.5),
    ("blocks", "Tapones", 0.1),
    ("steals", "Robos", 0.1),
]
LIMITES = {col: float(np.ceil(df[col].max())) for col, _, _ in FILTROS}


def control_filtro(col, etiqueta, paso):
    tope = LIMITES[col]
    salto = 10 if tope > 20 else (5 if tope > 8 else 1)
    marcas = {v: str(v) for v in range(0, int(tope) + 1, salto)}
    return html.Div(
        className="filtro-rango",
        children=[
            html.Div(etiqueta, className="etiqueta"),
            dcc.RangeSlider(
                id=f"filtro-{col}", min=0, max=tope, step=paso, value=[0, tope],
                marks=marcas, allowCross=False, updatemode="mouseup",
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ],
    )


def celda_kpi(id_kpi, titulo):
    return html.Div(
        className="kpi",
        children=[
            html.Div(titulo, className="kpi-titulo"),
            html.Div(id=f"kpi-{id_kpi}", className="kpi-valor"),
            html.Div(id=f"kpi-{id_kpi}-delta", className="kpi-delta"),
        ],
    )


CSS = """
body { margin: 0; background: __FONDO__; color: __TINTA__; font-family: __TEXTO__;
       -webkit-font-smoothing: antialiased; }

/* Cabecera */
.cabecera { background: __TINTA__; color: #fff; position: relative; overflow: hidden; }
/* Círculo central de la pista como único motivo decorativo */
.cabecera::after { content: ""; position: absolute; width: 420px; height: 420px; right: -60px; top: -150px;
                   border: 2px solid rgba(255,255,255,0.07); border-radius: 50%; pointer-events: none; }
.cabecera-fila { max-width: 1400px; margin: 0 auto; padding: 30px 32px 26px; display: flex;
                 justify-content: space-between; align-items: flex-end; gap: 24px; flex-wrap: wrap;
                 position: relative; z-index: 1; }
.cabecera h1 { font-family: __TITULOS__; font-weight: 600; font-size: 44px; line-height: 1;
               margin: 0; letter-spacing: 0.2px; }
.intro { color: #B9C2D3; margin: 10px 0 16px; max-width: 62ch; font-size: 15px; line-height: 1.5; }
.temporada { text-align: right; }
.temporada-etiqueta { color: #B9C2D3; font-size: 15px; }
.temporada-num { font-family: __TITULOS__; font-weight: 700; font-size: 120px; line-height: 0.85;
                 color: __BALON__; font-variant-numeric: tabular-nums; }

/* Chips con lo que se está viendo */
.chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { border: 1px solid rgba(255,255,255,0.28); border-radius: 999px; padding: 3px 11px;
        font-size: 13px; color: #fff; }
.chip-filtro { border-color: __BALON__; background: rgba(228,87,46,0.18); }

/* Contenido */
.contenido { max-width: 1400px; margin: 0 auto; padding: 0 32px 48px; }
.panel { background: __PANEL__; border: 1px solid __LINEA__; border-radius: 12px; padding: 18px 20px; }
.barra-temporada { margin-top: -1px; border-top: none; border-radius: 0 0 4px 4px; padding: 16px 28px 30px; background: #FCEDE7;}
.etiqueta { font-weight: 600; font-size: 14px; margin-bottom: 8px; }
.nota { font-size: 13px; color: __SUAVE__; line-height: 1.5; padding: 0 4px; }

/* Filtros plegables */
.filtros { margin-top: 16px; padding: 0; background: #FCEDE7;}
.filtros > summary { cursor: pointer; list-style: none; padding: 14px 20px; display: flex;
                     align-items: center; gap: 10px; font-family: __TITULOS__; font-size: 21px; font-weight: 600; }
.filtros > summary::-webkit-details-marker { display: none; }
.filtros > summary::before { content: "+"; width: 22px; height: 22px; border-radius: 50%;
                             border: 1.5px solid __TINTA__; display: inline-flex; align-items: center;
                             justify-content: center; font-family: __TEXTO__; font-size: 16px; line-height: 1; }
.filtros[open] > summary::before { content: "\\2212"; }
.filtros > summary .resumen { font-family: __TEXTO__; font-size: 14px; font-weight: 400; color: __SUAVE__; }
.filtros-cuerpo { padding: 4px 20px 22px; border-top: 1px solid __LINEA__; }
.fila-desplegables { display: flex; gap: 24px; flex-wrap: wrap; margin: 16px 0 22px; align-items: flex-end; }
.fila-desplegables > div { flex: 1 1 300px; }
.fila-rangos { display: flex; gap: 32px; flex-wrap: wrap; }
.filtro-rango { flex: 1 1 210px; min-width: 210px; }

.boton { font-family: __TEXTO__; font-size: 14px; font-weight: 500; color: __TINTA__; background: #fff;
         border: 1px solid __LINEA__; border-radius: 4px; padding: 8px 14px; cursor: pointer; flex: 0 0 auto !important; }
.boton:hover { border-color: __BALON__; color: __BALON__; }
.boton:focus-visible, summary:focus-visible { outline: 2px solid __BALON__; outline-offset: 2px; }

/* Marcador de KPIs */
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 16px; padding: 0; background: #FCEDE7; }
.kpi { padding: 18px 24px 16px; border-left: 1px solid __LINEA__; }
.kpi:first-child { border-left: none; }
.kpi-titulo { color: __SUAVE__; font-size: 14px; }
.kpi-valor { font-family: __TITULOS__; font-size: 56px; font-weight: 600; line-height: 1; margin-top: 8px;
             font-variant-numeric: tabular-nums; }
.kpi-delta { font-size: 13px; margin-top: 6px; }

/* Gráficos */
.graficos { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr); gap: 16px; margin-top: 16px;}
.panel-grafico { padding: 14px 16px 10px; background: #FCEDE7;}
.mariposa { margin-top: 16px; }

/* Sliders (rc-slider, el que usa dcc.Slider) */
.rc-slider-rail { background: #E3E6EA; }
.rc-slider-track { background: __BALON__; }
.rc-slider-handle { border: 2px solid __BALON__; background: #fff; opacity: 1; }
.rc-slider-handle:hover, .rc-slider-handle:active { border-color: __BALON__; box-shadow: 0 0 0 5px rgba(228,87,46,0.18); }
.rc-slider-dot { border-color: #D2D6DC; }
.rc-slider-dot-active { border-color: __BALON__; }
.rc-slider-mark-text { color: __SUAVE__; font-family: __TEXTO__; font-size: 12px; }
.rc-slider-mark-text-active { color: __TINTA__; }

/* Desplegables (dcc.Dropdown) */
.Select-control { border-color: __LINEA__ !important; border-radius: 4px !important; min-height: 40px; }
.is-focused:not(.is-open) > .Select-control { border-color: __BALON__ !important; box-shadow: none !important; }
.Select--multi .Select-value { background: #FCEDE7; border-color: #F3C1AE; color: #8A2A10; border-radius: 3px; }
.Select--multi .Select-value-icon { border-color: #F3C1AE; }
.Select-placeholder, .Select-input > input { font-family: __TEXTO__; }

@media (max-width: 1100px) { .graficos { grid-template-columns: 1fr; } }
@media (max-width: 760px) {
  .cabecera-fila, .contenido { padding-left: 16px; padding-right: 16px; }
  .cabecera h1 { font-size: 34px; }
  .temporada { text-align: left; }
  .temporada-num { font-size: 84px; }
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .kpi:nth-child(3) { border-left: none; }
  .kpi:nth-child(n+3) { border-top: 1px solid __LINEA__; }
  .kpi-valor { font-size: 44px; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""
for clave, valor in {"__FONDO__": FONDO, "__TINTA__": TINTA, "__BALON__": BALON, "__PANEL__": PANEL,
                     "__LINEA__": LINEA, "__SUAVE__": SUAVE, "__TITULOS__": FUENTE_TITULOS,
                     "__TEXTO__": FUENTE_TEXTO}.items():
    CSS = CSS.replace(clave, valor)




# 4. LAYOUT
# ============================================================================================================================================================================================================
app = Dash(__name__)
app.title = "La NBA, temporada a temporada"

# Fuentes de Google y CSS propio inyectados en la plantilla HTML de Dash
app.index_string = """<!DOCTYPE html>
<html lang="es">
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600;700&display=swap" rel="stylesheet">
{%css%}
<style>""" + CSS + """</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>"""

marcas = {int(t): str(t) for t in TEMPORADAS if t % 10 == 0}
marcas[T_MIN] = str(T_MIN)
marcas[T_MAX] = str(T_MAX)

CONFIG_GRAFICO = {"displaylogo": False,
                  "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}

app.layout = html.Div([
    html.Header(className="cabecera", children=[
        html.Div(className="cabecera-fila", children=[
            html.Div([
                html.H1("La NBA, temporada a temporada"),
                html.P("Rendimiento, origen y líderes de cada temporada desde 1960. "
                       "Elige un año, filtra por equipo o jugador, o pincha en el mapa.",
                       className="intro"),
                html.Div(id="subtitulo", className="chips"),
            ]),
            html.Div(className="temporada", children=[
                html.Div("Temporada", className="temporada-etiqueta"),
                html.Div(id="titulo-temporada", className="temporada-num"),
            ]),
        ]),
    ]),

    html.Main(className="contenido", children=[
        html.Div(className="panel barra-temporada", children=[
            dcc.Slider(
                id="slider-temporada",
                min=T_MIN, max=T_MAX, step=1, value=T_MAX,
                marks=marcas,
                tooltip={"placement": "bottom", "always_visible": False},
                updatemode="mouseup",   
            ),
        ]),

        html.Details(className="panel filtros", open=True, children=[
            html.Summary(["Filtros"]),
            html.Div(className="filtros-cuerpo", children=[
                html.Div(className="fila-desplegables", children=[
                    html.Div([
                        html.Div("Equipo", className="etiqueta"),
                        dcc.Dropdown(id="filtro-equipo", options=EQUIPOS_POR_TEMPORADA[T_MAX], value=[],
                                     multi=True, placeholder="Todos los equipos"),
                    ]),
                    html.Div([
                        html.Div("Jugador", className="etiqueta"),
                        dcc.Dropdown(id="filtro-jugador", options=OPCIONES_JUGADOR, value=[],
                                     multi=True, placeholder="Escribe un nombre para buscar"),
                    ]),
                    html.Button("Quitar todos los filtros", id="boton-reset", n_clicks=0,
                                className="boton"),
                    dcc.Store(id="seleccion-origen", data=[]),
                    dcc.Store(id="jugador-clicado", data=None),
                ]),
                html.Div(className="fila-rangos",
                         children=[control_filtro(*f) for f in FILTROS]),
            ]),
        ]),

        html.Div(className="panel kpis",
                 children=[celda_kpi(col, titulo) for col, titulo in KPIS]),

        html.Div(className="graficos", children=[
            html.Div(className="panel panel-grafico", children=[
                dcc.Graph(id="grafico-dispersion", config=CONFIG_GRAFICO),
            ]),
            html.Div(className="panel panel-grafico", children=[
                dcc.Graph(id="grafico-mapa", config=CONFIG_GRAFICO),
                html.Div("Pincha en un país o estado para ver solo a sus jugadores. "
                         "Vuelve a pincharlo para quitar el filtro.", className="nota"),
                html.Div(id="nota-mapa", className="nota"),
            ]),
        ]),

        html.Div(className="panel panel-grafico mariposa", children=[
            dcc.Graph(id="grafico-mariposa", config=CONFIG_GRAFICO),
        ]),
    ]),
])



# 5. FUNCIONES DE GRÁFICOS
# ============================================================================================================================================================================================================
def figura_dispersion(d, temporada, jugador=None):
    d = d[d["gamesPlayed"] >= MIN_PARTIDOS]
    hay_pm = d["plusMinusPoints"].notna().any()
    hover = ("<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
             "Minutos: %{x:.1f}<br>Puntos: %{y:.1f}<br>+/-: %{customdata[2]}<extra></extra>")
    pm_texto = d["plusMinusPoints"].map(lambda v: "s/d" if pd.isna(v) else f"{v:+.1f}")
    custom = np.column_stack([d["fullName"], d["equipos"], pm_texto,
                              d["personId"].astype(int), d["formacion"]])

    if hay_pm:
        lim = max(float(d["plusMinusPoints"].abs().quantile(1)), 1.0)
        marker = dict(
            size=9, color=d["plusMinusPoints"], colorscale=ESCALA_PM,
            cmin=-lim, cmax=lim, cmid=0,
            line=dict(width=0.6, color="#7A8494"),   
            colorbar=dict(title=dict(text="+/-", side="top"), thickness=10, outlinewidth=0,
                          len=0.75, tickfont=dict(color=SUAVE)),
            opacity=0.92,
        )
        titulo = ("Minutos y puntos" + subtitulo_grafico(
            f"{len(d)} jugadores con {MIN_PARTIDOS} o más partidos. El color es su +/- por partido."))
    else:
        marker = dict(size=9, color="#C4C9D0", line=dict(width=0.6, color="#7A8494"), opacity=0.92)
        titulo = ("Minutos y puntos" + subtitulo_grafico(
            f"{len(d)} jugadores con {MIN_PARTIDOS} o más partidos. El +/- no se registraba esta temporada."))

    fig = go.Figure(go.Scatter(
        x=d["numMinutes"], y=d["points"], mode="markers",
        marker=marker, customdata=custom, hovertemplate=hover,
    ))
    sel = d[d["personId"] == jugador] if jugador is not None else d.iloc[0:0]
    if len(sel):
        fig.add_trace(go.Scatter(
            x=sel["numMinutes"], y=sel["points"], mode="markers", hoverinfo="skip",
            marker=dict(size=20, color="rgba(0,0,0,0)", line=dict(width=3, color=BALON)),
            showlegend=False,
        ))
    fig.update_layout(
        title=dict(text=titulo),
        xaxis=dict(title="Minutos por partido"),
        yaxis=dict(title="Puntos por partido"),
        showlegend=False,
        margin=dict(l=50, r=10, t=78, b=50), height=520,
    )
    return fig


def figura_mapa(d, temporada, seleccion=None):
    seleccion = set(seleccion or [])
    conteo = (d.groupby(["formacion", "cod_estado", "cod_pais"], dropna=False)
                .size().reset_index(name="jugadores"))
    estados = conteo[conteo["cod_estado"].notna()]
    paises = conteo[conteo["cod_pais"].notna()]
    hover = "<b>%{customdata[0]}</b><br>Jugadores: %{customdata[1]}<extra></extra>"

    fig = go.Figure()
    for datos, cod, modo, nombre in [(paises, "cod_pais", "ISO-3", "Países"),
                                     (estados, "cod_estado", "USA-states", "Estados EE.UU.")]:
        elegido = datos["formacion"].isin(seleccion).to_numpy()
        if seleccion:
            opacidad = np.where(elegido, 1.0, 0.3)
            borde_color = np.where(elegido, TINTA, "white")
            borde_ancho = np.where(elegido, 2.5, 0.5)
        else:
            opacidad, borde_color, borde_ancho = 1.0, "white", 0.5
        fig.add_trace(go.Choropleth(
            locations=datos[cod], locationmode=modo,
            z=np.log10(datos["jugadores"]),
            customdata=datos[["formacion", "jugadores"]].values,
            hovertemplate=hover, coloraxis="coloraxis",
            marker=dict(opacity=opacidad, line=dict(color=borde_color, width=borde_ancho)),
            name=nombre,
        ))

    vacios = [e for e in ESTADOS_COD if e not in set(estados["formacion"])]
    if vacios:
        fig.add_trace(go.Choropleth(
            locations=[ESTADOS_COD[e] for e in vacios], locationmode="USA-states",
            z=[0] * len(vacios), colorscale=[[0, "#E6E8EC"], [1, "#E6E8EC"]], showscale=False,
            customdata=[[e, 0] for e in vacios], hovertemplate=hover,
            marker=dict(line=dict(color="#FFFFFF", width=0.6)), name="Sin jugadores",
        ))

    fig.update_layout(
        clickmode="event",
        title=dict(text="¿Dónde se formaron?" + subtitulo_grafico(
            "Estado o país en el que se formaron antes de llegar a la NBA, no donde nacieron.")),
        coloraxis=dict(
            colorscale=ESCALA_MAPA, cmin=0, cmax=np.log10(MAX_JUG),
            colorbar=dict(title=dict(text="Jugadores", side="top"), tickvals=np.log10(TICKS),
                          ticktext=[str(t) for t in TICKS], thickness=10, outlinewidth=0,
                          len=0.75, tickfont=dict(color=SUAVE)),
        ),
        geo=dict(projection_type="natural earth", showframe=False, bgcolor="rgba(0,0,0,0)",
                 showcoastlines=True, coastlinecolor="#B8BEC7", coastlinewidth=0.6,
                 showland=True, landcolor="#E6E8EC",
                 showcountries=True, countrycolor="white", showlakes=False),
        margin=dict(l=0, r=0, t=78, b=0), height=520,
    )
    fuera = int(d.loc[d["cod_estado"].isna() & d["cod_pais"].isna()].shape[0])
    return fig, fuera


TOP_N = 15
COLOR_AST = TINTA
COLOR_REB = BALON


def figura_mariposa(d, temporada, jugador=None):
    d = d[d["gamesPlayed"] >= 0]
    top_ast = d.nlargest(TOP_N, "assists")
    top_reb = d.nlargest(TOP_N, "reboundsTotal")

    maximo = np.nanmax([top_ast["assists"].max(), top_reb["reboundsTotal"].max(), 0])
    lim = max(15, int(np.ceil(maximo)))
    paso = 5 if lim <= 20 else 10
    ticks = list(range(0, lim + 1, paso))

    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.02,
                        subplot_titles=(f"Top {TOP_N} asistentes", f"Top {TOP_N} reboteadores"))

    for i, (top, col, nombre, color) in enumerate([
        (top_ast, "assists", "asistencias", COLOR_AST),
        (top_reb, "reboundsTotal", "rebotes", COLOR_REB),
    ], start=1):
        etiquetas = [f"{n}. {nom}" for n, nom in enumerate(top["fullName"], start=1)]
        fig.add_trace(go.Bar(
            y=etiquetas, x=top[col], orientation="h", marker_color=color,
            text=top[col].map("{:.1f}".format), textposition="inside", insidetextanchor="end",
            textangle=0,   # texto siempre horizontal
            textfont=dict(color="white", family=FUENTE_TITULOS, size=14),
            customdata=[[e, int(p), f] for e, p, f in
                        zip(top["equipos"], top["personId"], top["formacion"])],
            marker_line_color=[BALON if color == COLOR_AST else TINTA] * len(top),
            marker_line_width=[4 if p == jugador else 0 for p in top["personId"]],
            showlegend=False,
            hovertemplate=f"<b>%{{y}}</b><br>%{{customdata[0]}}<br>%{{x:.1f}} {nombre}<extra></extra>",
        ), row=1, col=i)
        fig.update_yaxes(categoryorder="array", categoryarray=etiquetas[::-1],  
                         side="left" if i == 1 else "right", row=1, col=i)

    fig.update_xaxes(range=[lim, 0], tickvals=[0], title_text="Asistencias por partido", row=1, col=1)
    fig.update_xaxes(range=[0, lim], tickvals=[0], title_text="Rebotes por partido", row=1, col=2)
    for anot, color in zip(fig.layout.annotations, [COLOR_AST, COLOR_REB]):
        anot.font = dict(family=FUENTE_TITULOS, size=18, color=color)

    fig.update_layout(
        title=dict(text="Líderes en asistencias y rebotes" + subtitulo_grafico(
            f"Media por partido. Solo jugadores con 3 o más partidos.")),
        bargap=0.28,
        margin=dict(l=20, r=20, t=110, b=50), height=580,
    )
    return fig



# 6. CALLBACK: todo se actualiza con el slider
# ============================================================================================================================================================================================================
@app.callback(
    Output("subtitulo", "children"),
    Output("titulo-temporada", "children"),
    *[Output(f"kpi-{c}", "children") for c, _ in KPIS],
    *[Output(f"kpi-{c}-delta", "children") for c, _ in KPIS],
    *[Output(f"kpi-{c}-delta", "style") for c, _ in KPIS],
    Output("grafico-dispersion", "figure"),
    Output("grafico-mapa", "figure"),
    Output("nota-mapa", "children"),
    Output("grafico-mariposa", "figure"),
    Input("slider-temporada", "value"),
    Input("seleccion-origen", "data"),
    Input("filtro-equipo", "value"),
    Input("filtro-jugador", "value"),
    Input("jugador-clicado", "data"),
    *[Input(f"filtro-{col}", "value") for col, _, _ in FILTROS],
)
def actualizar(temporada, origenes, equipos, jugadores, jugador_clic, *rangos):
    mascara = pd.Series(True, index=df.index)
    if jugadores:
        mascara &= df["personId"].isin(jugadores)
    # Equipo: entra el jugador si jugó en alguno de los equipos elegidos esa temporada
    if equipos:
        elegidos = set(equipos)
        mascara &= df["lista_equipos"].apply(lambda l: not elegidos.isdisjoint(l))
    # Rangos de los filtros numéricos (incluyendo los extremos)
    for (col, _, _), (lo, hi) in zip(FILTROS, rangos):
        mascara &= df[col].between(lo, hi)
    # El mapa usa los datos SIN filtro de origen: así se ven todos los
    # países/estados y se puede pinchar en otro; la selección se resalta.
    d_mapa = df[mascara & (df["season"] == temporada)]

    # Origen: lista vacía = todos
    if origenes:
        mascara &= df["formacion"].isin(origenes)
    dff = df[mascara]

    d = dff[dff["season"] == temporada]
    d_ant = dff[dff["season"] == temporada - 1]   # mismos filtros, para comparar igual con igual
    d_kpi, d_kpi_ant = d, d_ant
    if jugador_clic is not None:
        d_kpi = d[d["personId"] == jugador_clic]
        d_kpi_ant = d_ant[d_ant["personId"] == jugador_clic]

    valores, deltas, estilos = [], [], []
    for col, _ in KPIS:
        media = d_kpi[col].mean()
        valores.append(f"{media:.1f}" if len(d_kpi) else "–")
        if len(d_kpi) and len(d_kpi_ant):
            dif = media - d_kpi_ant[col].mean()
            deltas.append(f"{'▲' if dif >= 0 else '▼'} {abs(dif):.2f} vs {temporada - 1}")
            estilos.append({"fontSize": "13px", "marginTop": "2px",
                            "color": "#2E7D4F" if dif >= 0 else "#C0392B"})
        else:
            deltas.append("Sin jugadores con estos filtros" if not len(d_kpi)
                          else "Sin comparación con la temporada anterior")
            estilos.append({"fontSize": "13px", "marginTop": "2px", "color": COLOR_SUAVE})

    fig_mapa, fuera = figura_mapa(d_mapa, temporada, origenes)
    nota = f"{fuera} jugador(es) sin ubicación en el mapa (sin formación, G League Ignite, etc.)." if fuera else ""
    # Chips de la cabecera: nº de jugadores + cada filtro activo
    chips = [html.Span(f"{d['personId'].nunique()} jugadores", className="chip")]
    if jugador_clic is not None:
        chips.append(html.Span(f"Seleccionado: {NOMBRE_JUGADOR.get(jugador_clic, jugador_clic)}",
                               className="chip chip-filtro"))
    if origenes:
        chips.append(html.Span(f"Origen: {', '.join(origenes)}", className="chip chip-filtro"))
    if equipos:
        chips.append(html.Span(f"Equipo: {', '.join(equipos)}", className="chip chip-filtro"))
    if jugadores:
        nombres = [NOMBRE_JUGADOR.get(j, str(j)) for j in jugadores]
        chips.append(html.Span(f"Jugador: {', '.join(nombres)}", className="chip chip-filtro"))
    for (col, etiqueta, _), (lo, hi) in zip(FILTROS, rangos):
        if lo > 0 or hi < LIMITES[col]:
            chips.append(html.Span(f"{etiqueta}: {lo:g} a {hi:g}", className="chip chip-filtro"))
    subtitulo = chips

    return (subtitulo, str(temporada), *valores, *deltas, *estilos,
            figura_dispersion(d, temporada, jugador_clic), fig_mapa, nota,
            figura_mariposa(d, temporada, jugador_clic))


@app.callback(
    Output("seleccion-origen", "data"),
    Output("jugador-clicado", "data"),
    Output("filtro-equipo", "value"),
    Output("filtro-jugador", "value"),
    *[Output(f"filtro-{col}", "value") for col, _, _ in FILTROS],
    Output("grafico-mapa", "clickData"),
    Output("grafico-dispersion", "clickData"),
    Output("grafico-mariposa", "clickData"),
    Input("boton-reset", "n_clicks"),
    Input("grafico-mapa", "clickData"),
    Input("grafico-dispersion", "clickData"),
    Input("grafico-mariposa", "clickData"),
    State("seleccion-origen", "data"),
    State("jugador-clicado", "data"),
    prevent_initial_call=True,
)
def gestionar_filtros(_, click_mapa, click_disp, click_barras, origenes_actuales, jugador_actual):
    sin_cambios = [no_update] * len(FILTROS)
    limpiar_clicks = [None, None, None]

    def salida(origen=no_update, jugador=no_update):
        return [origen, jugador, no_update, no_update] + sin_cambios + limpiar_clicks

    disparador = ctx.triggered_id

    if disparador == "boton-reset":
        return [[], None, [], []] + [[0, LIMITES[col]] for col, _, _ in FILTROS] + limpiar_clicks

    if disparador == "grafico-mapa":
        if not click_mapa:
            return [no_update] * (4 + len(FILTROS) + 3)
        origen, n_jugadores = click_mapa["points"][0]["customdata"][:2]
        if not n_jugadores:
            return salida()
        nuevo = [] if origenes_actuales == [origen] else [origen]
        return salida(origen=nuevo, jugador=None)

    click = click_disp if disparador == "grafico-dispersion" else click_barras
    if not click:
        return [no_update] * (4 + len(FILTROS) + 3)
    datos = click["points"][0].get("customdata")
    if not datos:
        return salida()
    if disparador == "grafico-dispersion":
        pid, origen = int(float(datos[3])), datos[4]
    else:
        pid, origen = int(datos[1]), datos[2]

    if pid == jugador_actual:
        return salida(origen=[], jugador=None)
    return salida(origen=[origen], jugador=pid)


@app.callback(
    Output("filtro-equipo", "options"),
    Output("filtro-equipo", "value", allow_duplicate=True),
    Input("slider-temporada", "value"),
    State("filtro-equipo", "value"),
    prevent_initial_call=True,
)
def equipos_temporada(temporada, seleccionados):
    opciones = EQUIPOS_POR_TEMPORADA.get(temporada, [])
    seleccionados = seleccionados or []
    validos = [e for e in seleccionados if e in opciones]
    return opciones, validos if validos != seleccionados else no_update


if __name__ == "__main__":
    app.run(debug=True)
