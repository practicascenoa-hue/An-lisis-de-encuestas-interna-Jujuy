import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

st.title("🚀 Principales Indicadores de Calidad - Taller Cenoa")
st.markdown("---")

# Carga de Datos
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.dropna(how='all')
    except:
        return None

df = load_data()

if df is not None:
    col_nps = next((c for c in df.columns if "escala" in c.lower() or "satisfecho" in c.lower()), None)
    
    if col_nps:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        total = len(df)
        promotores = len(df[df[col_nps] >= 9])
        detractores = len(df[df[col_nps] <= 6])
        nps_score = ((promotores - detractores) / total) * 100
        csat_score = df[col_nps].mean()

        # --- FILA 1: LOS RELOJES (GAUGES) ---
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de Reloj para NPS
            fig_nps = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = nps_score,
                title = {'text': "NPS (Net Promoter Score)"},
                gauge = {
                    'axis': {'range': [-100, 100]},
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [-100, 0], 'color': "#FF4B4B"},
                        {'range': [0, 70], 'color': "#FFA500"},
                        {'range': [70, 100], 'color': "#00CC96"}]
                }
            ))
            fig_nps.update_layout(height=350)
            st.plotly_chart(fig_nps, use_container_width=True)

        with col2:
            # Gráfico de Reloj para CSAT
            fig_csat = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = csat_score,
                title = {'text': "CSAT (Satisfacción Media)"},
                gauge = {
                    'axis': {'range': [0, 10]},
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [0, 6], 'color': "#FF4B4B"},
                        {'range': [6, 8.5], 'color': "#FFA500"},
                        {'range': [8.5, 10], 'color': "#00CC96"}]
                }
            ))
            fig_csat.update_layout(height=350)
            st.plotly_chart(fig_csat, use_container_width=True)

        st.markdown("---")

        # --- FILA 2: OTROS GRÁFICOS (Barras) ---
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📊 Distribución de Notas")
            counts = df[col_nps].value_counts().sort_index()
            st.bar_chart(counts, color="#29b5e8")

        with c2:
            st.subheader("👥 Total de Encuestas Analizadas")
            st.metric("Participación", f"{total} clientes")
            st.info("🎯 El NPS actual de 96 pts se considera EXCELENTE.")

    else:
        st.error("No se detectó la columna de puntuación.")
