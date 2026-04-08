import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración del Portal
st.set_page_config(page_title="Dashboard Chapa y Pintura", layout="wide")

st.title("🚗 Panel de Indicadores - Taller de Chapa y Pintura")
st.markdown("---")

# 2. Carga de Datos
@st.cache_data(ttl=300)
def load_data():
    sheet_id = "1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y"
    sheet_name = "Resp.%20de%20form.%20de%20Satisf."
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()

    # --- DEFINICIÓN DE PREGUNTAS (Tal cual las escribiste) ---
    p_nps = "¿Qué tan probable es que recomiendes el servicio del Taller de Chapa y Pintura a familiares o amigos?"
    p_tiempo = "¿Qué tan satisfecho estás con el tiempo que tardaron en completar la reparación?"
    p_calidad = "¿Cómo calificarías la calidad del trabajo de chapa y pintura realizado en su vehículo?\""
    p_ambiente = "¿Cuán satisfecho estuvo con el ambiente del Taller (recepción del servicio, estacionamiento del cliente, zona de espera, etc.)?"
    p_asesor = "¿Cuán satisfecho estuvo con la atención, cortesía y claridad del Asesor de Servicio para explicarle el trabajo y responder sus consultas?"
    p_turno = "¿Cuán satisfecho estuvo con la facilidad para obtener un turno que se adapte a sus necesidades?"

    # --- SECCIÓN 1: MÉTRICAS PRINCIPALES ---
    col1, col2, col3 = st.columns(3)

    # Indicador 1: NPS (Lealtad)
    if p_nps in df.columns:
        nps_data = pd.to_numeric(df[p_nps], errors='coerce').dropna()
        promotores = len(nps_data[nps_data >= 9])
        detractores = len(nps_data[nps_data <= 6])
        nps_score = ((promotores - detractores) / len(nps_data)) * 100 if len(nps_data) > 0 else 0
        col1.metric("NPS (Net Promoter Score)", f"{int(nps_score)}", help="Objetivo: >70")

    # Indicador 2: Calidad Percibida (Promedio)
    if p_calidad in df.columns:
        avg_calidad = pd.to_numeric(df[p_calidad], errors='coerce').mean()
        col2.metric("Índice de Calidad", f"{avg_calidad:.2f} / 10")

    # Indicador 3: Eficiencia en Tiempos
    if p_tiempo in df.columns:
        avg_tiempo = pd.to_numeric(df[p_tiempo], errors='coerce').mean()
        col3.metric("Satisfacción Tiempo", f"{avg_tiempo:.2f} / 10")

    st.markdown("---")

    # --- SECCIÓN 2: ANÁLISIS POR CATEGORÍA ---
    st.header("Análisis de Procesos")
    c1, c2 = st.columns(2)

    with c1:
        # Gráfico de Radar o Barras para comparar áreas
        indicadores = {
            "Turnos": pd.to_numeric(df[p_turno], errors='coerce').mean() if p_turno in df.columns else 0,
            "Asesor": pd.to_numeric(df[p_asesor], errors='coerce').mean() if p_asesor in df.columns else 0,
            "Ambiente": pd.to_numeric(df[p_ambiente], errors='coerce').mean() if p_ambiente in df.columns else 0
        }
        df_radar = pd.DataFrame(dict(r=list(indicadores.values()), theta=list(indicadores.keys())))
        fig_radar = px.line_polar(df_radar, r='r', theta='theta', line_close=True, title="Puntajes por Área (Escala 1-10)")
        fig_radar.update_traces(fill='toself')
        st.plotly_chart(fig_radar, use_container_width=True)

    with c2:
        # Histograma de calidad del trabajo
        if p_calidad in df.columns:
            fig_hist = px.histogram(df, x=p_calidad, nbins=10, 
                                   title="Distribución de Calidad del Trabajo",
                                   color_discrete_sequence=['#2ecc71'])
            fig_hist.update_layout(xaxis_title="Calificación", yaxis_title="Cantidad de Clientes")
            st.plotly_chart(fig_hist, use_container_width=True)

    # --- SECCIÓN 3: TABLA DE ALERTAS ---
    st.markdown("---")
    st.subheader("⚠️ Clientes Detractores (Calificación baja en Recomendación)")
    if p_nps in df.columns:
        detractores_df = df[pd.to_numeric(df[p_nps], errors='coerce') <= 6]
        if not detractores_df.empty:
            st.warning(f"Se han detectado {len(detractores_df)} clientes insatisfechos.")
            st.write(detractores_df)
        else:
            st.success("¡No hay detractores registrados!")

except Exception as e:
    st.error(f"Error al procesar el tablero: {e}")
    st.info("Asegúrate de que los nombres de las columnas en el Sheet coincidan exactamente con las preguntas.")
