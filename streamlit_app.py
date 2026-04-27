import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")
st.title("🚀 Dashboard de Calidad Cenoa")

# Carga de Datos
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.dropna(how='all')
    except: return None

df = load_data()

if df is not None:
    # 1. Búsqueda de columna de nota (NPS/CSAT)
    col_nps = next((c for c in df.columns if "escala" in c.lower() or "satisfecho" in c.lower()), None)
    
    if col_nps:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        total = len(df)
        promotores = len(df[df[col_nps] >= 9])
        detractores = len(df[df[col_nps] <= 6])
        nps_score = ((promotores - detractores) / total) * 100
        csat_score = df[col_nps].mean()

        # --- FILA 1: RELOJES (NPS y CSAT) ---
        c1, c2 = st.columns(2)
        with c1:
            fig_nps = go.Figure(go.Indicator(
                mode = "gauge+number", value = nps_score, title = {'text': "NPS Global"},
                gauge = {'axis': {'range': [-100, 100]}, 'bar': {'color': "black"},
                         'steps': [{'range': [-100, 0], 'color': "#FF4B4B"},
                                   {'range': [0, 70], 'color': "#FFA500"},
                                   {'range': [70, 100], 'color': "#00CC96"}]}))
            st.plotly_chart(fig_nps, use_container_width=True)
        with c2:
            fig_csat = go.Figure(go.Indicator(
                mode = "gauge+number", value = csat_score, title = {'text': "CSAT (Promedio)"},
                gauge = {'axis': {'range': [0, 10]}, 'bar': {'color': "black"},
                         'steps': [{'range': [0, 6], 'color': "#FF4B4B"},
                                   {'range': [6, 8.5], 'color': "#FFA500"},
                                   {'range': [8.5, 10], 'color': "#00CC96"}]}))
            st.plotly_chart(fig_csat, use_container_width=True)

        st.markdown("---")
        st.header("🔍 Análisis por Pilares de Procesos")

        # --- FILA 2: INDICADORES DE PROCESO (SÍ/NO) ---
        # Definimos las palabras clave para encontrar las preguntas de proceso
        pilares = {
            "🛠️ Reparación (FIR)": "solucionado",
            "💰 Explicación Factura": "explicaron",
            "⏰ Entrega a Tiempo": "acordada",
            "✨ Limpieza": "limpieza"
        }

        cols = st.columns(len(pilares))
        
        for i, (nombre, clave) in enumerate(pilares.items()):
            # Buscamos la columna que contenga la palabra clave
            col_pilar = next((c for c in df.columns if clave in c.lower()), None)
            
            with cols[i]:
                if col_pilar:
                    # Calculamos el % de "Sí"
                    si_count = len(df[df[col_pilar].astype(str).str.lower().str.contains("sí|si|yes")])
                    pct = (si_count / total) * 100
                    st.metric(nombre, f"{int(pct)}%")
                    st.progress(pct / 100)
                else:
                    st.caption(f"No se encontró: {nombre}")

        st.markdown("---")
        st.subheader("📋 Detalle de Comentarios")
        # Buscamos la columna de comentarios o sugerencias
        col_coment = next((c for c in df.columns if "comentario" in c.lower() or "sugerencia" in c.lower() or "porque" in c.lower()), None)
        if col_coment:
            st.dataframe(df[[col_coment]].dropna(), use_container_width=True)

    else: st.error("No se detectó la columna de puntuación.")
