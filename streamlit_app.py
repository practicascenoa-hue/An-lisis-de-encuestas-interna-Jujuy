import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Dashboard Autolux / Cenoa", layout="wide")

st.title("🚀 Panel de Control de Calidad y Satisfacción")
st.markdown("---")

# 2. Carga de datos
@st.cache_data(ttl=600)
def load_data():
    sheet_id = "1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y"
    sheet_name = "Resp.%20de%20form.%20de%20Satisf."
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    # Limpieza básica de nombres de columnas (quitar espacios extras)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()

    # --- SECCIÓN 1: MÉTRICAS CLAVE (KPIs) ---
    st.header("📊 Indicadores Globales")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    # A. Cálculo de NPS (Basado en la columna de recomendación)
    # Ajusta el nombre si en tu sheet es diferente
    col_nps = "Qué tan probable es que nos recomiende con un familiar o amigo?"
    if col_nps in df.columns:
        nps_data = pd.to_numeric(df[col_nps], errors='coerce').dropna()
        promotores = len(nps_data[nps_data >= 9])
        detractores = len(nps_data[nps_data <= 6])
        total_nps = len(nps_data)
        nps_score = ((promotores - detractores) / total_nps) * 100 if total_nps > 0 else 0
        kpi1.metric("Net Promoter Score", f"{int(nps_score)} pts", delta="Objetivo: >70")
    else:
        kpi1.info("Columna NPS no hallada")

    # B. Facilidad de Turno (Promedio)
    col_turno = "Cuán satisfecho estuvo con la facilidad para obtener un turno que se adapte a sus necesidades?"
    if col_turno in df.columns:
        avg_turno = pd.to_numeric(df[col_turno], errors='coerce').mean()
        kpi2.metric("Facilidad de Turno", f"{avg_turno:.2f} / 5")

    # C. Resolución Técnica (Fix It Right)
    # Suponiendo una pregunta de Sí/No o escala de solución
    col_fix = "Se solucionó el inconveniente por el cual trajo su vehículo en esta visita?"
    if col_fix in df.columns:
        # Contamos los "Sí" o valores altos
        exito = len(df[df[col_fix].astype(str).str.contains("Sí|5|4", case=False)])
        pct_fix = (exito / len(df)) * 100
        kpi3.metric("Fix It Right (1ra Visita)", f"{pct_fix:.1f}%")

    # D. Total de Encuestas
    kpi4.metric("Encuestas Totales", len(df))

    st.markdown("---")

    # --- SECCIÓN 2: GRÁFICOS DETALLADOS ---
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("👨‍💼 Desempeño por Asesor")
        col_asesor = "Nombre del Asesor de Servicio" # Ajustar según tu sheet
        col_sat_asesor = "Cómo calificaría la atención de su asesor de servicios?"
        
        if col_asesor in df.columns and col_sat_asesor in df.columns:
            df[col_sat_asesor] = pd.to_numeric(df[col_sat_asesor], errors='coerce')
            ranking = df.groupby(col_asesor)[col_sat_asesor].mean().sort_values(ascending=True).reset_index()
            fig_asesor = px.bar(ranking, x=col_sat_asesor, y=col_asesor, orientation='h',
                                title="Promedio de Calificación por Asesor",
                                color=col_sat_asesor, color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_asesor, use_container_width=True)
        else:
            st.warning("Para ver el ranking, verifica los nombres de las columnas de Asesor.")

    with col_der:
        st.subheader("📅 Tendencia de Satisfacción")
        col_fecha = "Marca temporal" # Nombre estándar de Google Forms
        if col_fecha in df.columns:
            df[col_fecha] = pd.to_datetime(df[col_fecha])
            # Agrupar por día o mes y sacar promedio de una columna de satisfacción
            df_hist = df.set_index(col_fecha).resample('D')[col_turno].mean().reset_index()
            fig_hist = px.line(df_hist, x=col_fecha, y=col_turno, title="Evolución Diaria (Satisfacción Turnos)")
            st.plotly_chart(fig_hist, use_container_width=True)

    # --- SECCIÓN 3: NUBE DE COMENTARIOS ---
    st.markdown("---")
    st.subheader("💬 Comentarios de Clientes")
    col_comentarios = "Comentarios o sugerencias" # Ajustar nombre
    if col_comentarios in df.columns:
        ultimos_comentarios = df[col_comentarios].dropna().tail(10)
        for c in ultimos_comentarios:
            st.info(c)

except Exception as e:
    st.error(f"Error general en el dashboard: {e}")
