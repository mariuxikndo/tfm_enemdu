"""
webapp/components/charts.py
────────────────────────────────────────────────────────────────────
Biblioteca de gráficos Plotly reutilizables para la plataforma.

Corrección: margin eliminado de _LAYOUT_BASE para evitar
"multiple values for keyword argument 'margin'" al hacer
update_layout(**_LAYOUT_BASE, margin=...).
"""

from __future__ import annotations
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Paleta base ───────────────────────────────────────────────────
COLORES_DIM = {
    "agua":       "#1A6F9C",
    "residuos":   "#2D8C3F",
    "energia":    "#D97706",
    "movilidad":  "#7C3AED",
    "conciencia": "#C0392B",
}

_FONT = "Inter, sans-serif"
_BG   = "rgba(0,0,0,0)"

# margin NO está aquí — cada función lo pasa explícitamente
_LAYOUT_BASE = dict(
    font_family=_FONT,
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    hoverlabel=dict(font_family=_FONT, font_size=13),
)

_MARGIN_DEFAULT = dict(l=10, r=10, t=40, b=10)
_MARGIN_GAUGE   = dict(l=20, r=20, t=40, b=10)
_MARGIN_DONA    = dict(l=10, r=10, t=40, b=60)


# ── Tarjeta KPI ───────────────────────────────────────────────────

def kpi_card(
    valor:     float,
    etiqueta:  str,
    unidad:    str   = "%",
    dimension: str   = "agua",
    n_muestra: int   = None,
) -> None:
    """Renderiza una tarjeta KPI con HTML/CSS."""
    color     = COLORES_DIM.get(dimension, "#1A6F9C")
    valor_str = f"{valor:.1f}" if valor is not None else "—"
    muestra   = f"n = {n_muestra:,}" if n_muestra else ""

    st.markdown(f"""
    <div class="kpi-card dim-{dimension}">
        <div class="kpi-value" style="color:{color};">{valor_str}
            <span style="font-size:1rem;font-weight:400;color:#9CA3AF;">{unidad}</span>
        </div>
        <div class="kpi-label">{etiqueta}</div>
        <div class="kpi-unit">{muestra}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Barras horizontales ───────────────────────────────────────────

def barras_horizontal(
    df:      pd.DataFrame,
    col_y:   str,
    col_x:   str   = "valor",
    titulo:  str   = "",
    color:   str   = "#1A6F9C",
    unidad:  str   = "%",
    max_val: float = 100,
) -> go.Figure:
    """Gráfico de barras horizontales."""
    if df.empty or col_x not in df.columns or col_y not in df.columns:
        return _fig_vacia("Sin datos disponibles")

    df_p = df.dropna(subset=[col_x]).sort_values(col_x, ascending=True)

    fig = go.Figure(go.Bar(
        x=df_p[col_x], y=df_p[col_y],
        orientation="h",
        marker_color=color, marker_line_width=0,
        text=df_p[col_x].apply(lambda v: f"{v:.1f}{unidad}"),
        textposition="outside",
        textfont=dict(size=12, color="#374151"),
        hovertemplate=f"<b>%{{y}}</b><br>%{{x:.1f}}{unidad}<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        margin=_MARGIN_DEFAULT,          # ← aquí, no en _LAYOUT_BASE
        title=dict(text=titulo, font=dict(size=13, color="#374151"), x=0),
        xaxis=dict(
            range=[0, min(max_val * 1.15, 110)],
            showgrid=True, gridcolor="#F0F0F0",
            ticksuffix=unidad, tickfont=dict(size=11), zeroline=False,
        ),
        yaxis=dict(tickfont=dict(size=11, color="#374151"), automargin=True),
        height=max(250, len(df_p) * 36 + 60),
        bargap=0.3,
    )
    return fig


# ── Barras comparativas (dos grupos) ─────────────────────────────

def barras_comparativas(
    df:        pd.DataFrame,
    col_y:     str,
    col_x:     str = "valor",
    col_grupo: str = "grupo",
    label_a:   str = "Grupo A",
    label_b:   str = "Grupo B",
    unidad:    str = "%",
    titulo:    str = "",
) -> go.Figure:
    """Barras agrupadas para comparar dos grupos."""
    if df.empty:
        return _fig_vacia("Sin datos comparativos")

    df_a = df[df[col_grupo] == "A"]
    df_b = df[df[col_grupo] == "B"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_a[col_x], y=df_a[col_y], name=label_a,
        orientation="h", marker_color="#1A6F9C",
        hovertemplate=f"<b>%{{y}}</b><br>{label_a}: %{{x:.1f}}{unidad}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df_b[col_x], y=df_b[col_y], name=label_b,
        orientation="h", marker_color="#E8A87C",
        hovertemplate=f"<b>%{{y}}</b><br>{label_b}: %{{x:.1f}}{unidad}<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        margin=_MARGIN_DEFAULT,
        title=dict(text=titulo, font=dict(size=13, color="#374151"), x=0),
        barmode="group",
        xaxis=dict(ticksuffix=unidad, showgrid=True, gridcolor="#F0F0F0"),
        yaxis=dict(tickfont=dict(size=11), automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=max(280, len(df_a) * 48 + 80),
    )
    return fig


# ── Barras por área (urbano/rural) ────────────────────────────────

def barras_area(
    df:        pd.DataFrame,
    col_y:     str   = "indicador",
    col_x:     str   = "valor",
    col_area:  str   = "area_nombre",
    unidad:    str   = "%",
    titulo:    str   = "",
    color_urb: str   = "#1A6F9C",
    color_rur: str   = "#6CB6D9",
) -> go.Figure:
    """Barras agrupadas por área urbana/rural."""
    if df.empty:
        return _fig_vacia("Sin datos por área")

    df_u = df[df[col_area] == "Urbano"] if col_area in df.columns else pd.DataFrame()
    df_r = df[df[col_area] == "Rural"]  if col_area in df.columns else pd.DataFrame()

    fig = go.Figure()
    if not df_u.empty:
        fig.add_trace(go.Bar(
            x=df_u[col_x], y=df_u[col_y], name="Urbano",
            orientation="h", marker_color=color_urb,
            text=df_u[col_x].apply(lambda v: f"{v:.1f}{unidad}"),
            textposition="outside",
        ))
    if not df_r.empty:
        fig.add_trace(go.Bar(
            x=df_r[col_x], y=df_r[col_y], name="Rural",
            orientation="h", marker_color=color_rur,
            text=df_r[col_x].apply(lambda v: f"{v:.1f}{unidad}"),
            textposition="outside",
        ))
    fig.update_layout(
        **_LAYOUT_BASE,
        margin=_MARGIN_DEFAULT,
        title=dict(text=titulo, font=dict(size=13, color="#374151"), x=0),
        barmode="group",
        xaxis=dict(ticksuffix=unidad, showgrid=True, gridcolor="#F0F0F0", range=[0, 115]),
        yaxis=dict(tickfont=dict(size=11), automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        height=max(250, len(df_u) * 48 + 80),
    )
    return fig


# ── Mapa de provincias ────────────────────────────────────────────

def mapa_provincias(
    df:        pd.DataFrame,
    col_prov:  str   = "prov",
    col_valor: str   = "valor",
    titulo:    str   = "",
    color:     str   = "#1A6F9C",
    unidad:    str   = "%",
) -> go.Figure:
    """Barras ordenadas por provincia (sustituto de coropleta)."""
    if df.empty or col_valor not in df.columns:
        return _fig_vacia("Sin datos por provincia")

    PROV_NOMBRES = {
        1:"Azuay", 2:"Bolívar", 3:"Cañar", 4:"Carchi",
        5:"Cotopaxi", 6:"Chimborazo", 7:"El Oro", 8:"Esmeraldas",
        9:"Guayas", 10:"Imbabura", 11:"Loja", 12:"Los Ríos",
        13:"Manabí", 14:"Morona Santiago", 15:"Napo", 16:"Pastaza",
        17:"Pichincha", 18:"Tungurahua", 19:"Zamora Chinchipe",
        20:"Galápagos", 21:"Sucumbíos", 22:"Orellana",
        23:"Santo Domingo", 24:"Santa Elena",
    }

    df_p = df.copy()
    if "prov_nombre" not in df_p.columns and col_prov in df_p.columns:
        df_p["prov_nombre"] = pd.to_numeric(df_p[col_prov], errors="coerce").map(PROV_NOMBRES)

    col_etq = "prov_nombre" if "prov_nombre" in df_p.columns else col_prov
    df_p    = df_p.dropna(subset=[col_valor]).sort_values(col_valor, ascending=True)

    fig = go.Figure(go.Bar(
        x=df_p[col_valor], y=df_p[col_etq],
        orientation="h",
        marker_color=color, marker_opacity=0.8,
        text=df_p[col_valor].apply(lambda v: f"{v:.1f}{unidad}"),
        textposition="outside",
        hovertemplate=f"<b>%{{y}}</b><br>%{{x:.1f}}{unidad}<extra></extra>",
    ))
    n = len(df_p)
    fig.update_layout(
        **_LAYOUT_BASE,
        margin=_MARGIN_DEFAULT,
        title=dict(text=titulo, font=dict(size=13, color="#374151"), x=0),
        xaxis=dict(ticksuffix=unidad, showgrid=True, gridcolor="#F0F0F0", range=[0, 115]),
        yaxis=dict(tickfont=dict(size=10), automargin=True),
        height=max(400, n * 22 + 80),
        bargap=0.2,
    )
    return fig


# ── Dona / pie ────────────────────────────────────────────────────

def dona_distribucion(
    labels:  list,
    values:  list,
    titulo:  str  = "",
    colores: list = None,
) -> go.Figure:
    """Gráfico de dona para distribución de categorías."""
    if not labels or not values:
        return _fig_vacia("Sin datos")

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.5,
        marker_colors=colores or px.colors.qualitative.Set2,
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        margin=_MARGIN_DONA,             # ← margen mayor para la leyenda
        title=dict(text=titulo, font=dict(size=13, color="#374151"), x=0.5, xanchor="center"),
        height=300,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
        showlegend=True,
    )
    return fig


# ── Gauge de índice ───────────────────────────────────────────────

def gauge_indice(
    valor:  float,
    maximo: float,
    titulo: str   = "",
    color:  str   = "#1A6F9C",
    unidad: str   = "pts",
) -> go.Figure:
    """Gauge para visualizar un índice compuesto."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor if valor is not None else 0,
        number=dict(suffix=f" {unidad}", font=dict(size=28, color="#1A2332")),
        title=dict(text=titulo, font=dict(size=12, color="#6B7280")),
        gauge=dict(
            axis=dict(range=[0, maximo], tickfont=dict(size=10)),
            bar=dict(color=color, thickness=0.3),
            bgcolor="#F4F7FB",
            borderwidth=0,
            steps=[
                dict(range=[0, maximo * 0.33], color="#E8F4E8"),
                dict(range=[maximo * 0.33, maximo * 0.66], color="#C8E6C9"),
                dict(range=[maximo * 0.66, maximo], color="#A5D6A7"),
            ],
        ),
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        margin=_MARGIN_GAUGE,            # ← margen propio del gauge
        height=200,
    )
    return fig


# ── Utilidad interna ──────────────────────────────────────────────

def _fig_vacia(mensaje: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=mensaje, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="#9CA3AF"),
    )
    fig.update_layout(**_LAYOUT_BASE, margin=_MARGIN_DEFAULT, height=200)
    return fig
