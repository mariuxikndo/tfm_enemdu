"""webapp/pages/6_Comparativo.py — Análisis comparativo entre grupos."""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Comparativo · MIAH-ENEMDU", page_icon="⚖️", layout="wide")

from webapp.components.sidebar_filters import render_sidebar_comparativo
from webapp.components.charts import barras_comparativas
from webapp.data_layer import cargar_comparativa, mostrar_error_sin_datos, NOMBRES_DIMENSION

CSS = """<style>
.stApp{background-color:#F4F7FB;}
[data-testid="stSidebar"]{background-color:#1A2332;}
[data-testid="stSidebar"] *{color:#E8EDF3!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.5rem;}
</style>"""

st.markdown(CSS, unsafe_allow_html=True)

# ── Sidebar comparativo ───────────────────────────────────────────
fa, fb = render_sidebar_comparativo()

# ── Encabezado ────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:20px;">
    <h1 style="font-size:1.4rem;font-weight:600;color:#1A2332;margin:0;">
        ⚖️ Análisis Comparativo
    </h1>
    <p style="color:#6B7280;font-size:.88rem;margin:4px 0 0;">
        <span style="color:#1A6F9C;font-weight:600;">🔵 {fa['label']}</span>
        &nbsp;vs&nbsp;
        <span style="color:#D97706;font-weight:600;">🟠 {fb['label']}</span>
    </p>
</div>""", unsafe_allow_html=True)

# ── Selección de dimensión ────────────────────────────────────────
dim_opciones = {v: k for k, v in NOMBRES_DIMENSION.items()}
dim_sel = st.selectbox(
    "Selecciona la dimensión a comparar",
    options=list(dim_opciones.keys()),
    index=0,
)
dimension = dim_opciones[dim_sel]

st.markdown("---")

# ── Calcular comparativa ──────────────────────────────────────────
if st.button("🔄 Calcular comparativa", type="primary"):
    with st.spinner(f"Calculando {dim_sel} para ambos grupos..."):
        try:
            df_comp = cargar_comparativa(
                dimension,
                area_a=fa.get("area"), prov_a=fa.get("prov"),
                area_b=fb.get("area"), prov_b=fb.get("prov"),
            )
        except Exception as e:
            mostrar_error_sin_datos()
            st.error(str(e))
            st.stop()

    if df_comp.empty:
        st.warning("Sin datos para la comparativa seleccionada.")
        st.stop()

    # ── Tabla de diferencias ──────────────────────────────────────
    df_a = df_comp[df_comp["grupo"] == "A"][["indicador_id","indicador","valor"]].rename(
        columns={"valor": f"Grupo A ({fa['label']})"})
    df_b = df_comp[df_comp["grupo"] == "B"][["indicador_id","valor"]].rename(
        columns={"valor": f"Grupo B ({fb['label']})"})
    df_tabla = df_a.merge(df_b, on="indicador_id", how="outer")
    col_a = f"Grupo A ({fa['label']})"
    col_b = f"Grupo B ({fb['label']})"
    df_tabla["Diferencia (A-B)"] = (df_tabla[col_a] - df_tabla[col_b]).round(2)
    df_tabla["Variación (%)"] = (
        (df_tabla[col_a] - df_tabla[col_b]) / df_tabla[col_b].abs() * 100
    ).round(1).apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")

    # ── Gráfico comparativo ───────────────────────────────────────
    st.markdown(f"**{dim_sel} — comparativa**")
    fig = barras_comparativas(
        df_comp,
        col_y="indicador",
        col_x="valor",
        col_grupo="grupo",
        label_a=fa["label"],
        label_b=fb["label"],
        titulo="",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabla resumen ─────────────────────────────────────────────
    st.markdown("**Tabla de diferencias**")
    st.dataframe(
        df_tabla.drop(columns=["indicador_id"]),
        use_container_width=True,
        hide_index=True,
    )

    # ── Exportar ──────────────────────────────────────────────────
    csv = df_tabla.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ Descargar tabla comparativa",
        csv,
        file_name=f"comparativa_{dimension}_{fa['label']}_vs_{fb['label']}.csv",
        mime="text/csv",
    )

    # ── Resumen automático ────────────────────────────────────────
    st.markdown("---")
    st.markdown("**Resumen automático**")
    mejoras = df_tabla[df_tabla["Diferencia (A-B)"] > 0]["indicador"].tolist()
    retrocesos = df_tabla[df_tabla["Diferencia (A-B)"] < 0]["indicador"].tolist()
    if mejoras:
        st.success(
            f"El Grupo A ({fa['label']}) supera al Grupo B en: "
            + ", ".join(mejoras[:3])
            + ("..." if len(mejoras) > 3 else ".")
        )
    if retrocesos:
        st.warning(
            f"El Grupo B ({fb['label']}) supera al Grupo A en: "
            + ", ".join(retrocesos[:3])
            + ("..." if len(retrocesos) > 3 else ".")
        )

else:
    st.info(
        "Configura los dos grupos en el panel lateral y pulsa "
        "**Calcular comparativa** para ver los resultados."
    )
    st.markdown("""
    **Ejemplos de comparativas útiles:**
    - 🏙️ Urbano vs 🌾 Rural — ¿Quién tiene mejores prácticas ambientales?
    - 🗺️ Pichincha vs Guayas — Diferencias entre las dos principales provincias
    - ✅ Nacional vs una provincia específica
    """)

st.markdown("""<p style="text-align:center;color:#9CA3AF;font-size:.72rem;margin-top:24px;">
Fuente: INEC Ecuador · MIAH-ENEMDU 2025 · Resultados ponderados con fexp</p>""",
unsafe_allow_html=True)
