import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("Seleccionar fecha para filtrar análisis")

# Selector de Rango de Fechas con formato DD-MM-YYYY
st.sidebar.subheader("Calendario")
fecha_inicio = st.sidebar.date_input("Fecha Inicio", datetime(2026, 1, 1), format="DD/MM/YYYY")
fecha_fin = st.sidebar.date_input("Fecha Fin", datetime.now(), format="DD/MM/YYYY")

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Buscar columna de fecha automáticamente
        col_fecha = next((c for c in df.columns if "fecha" in c.lower() or "marca temporal" in c.lower()), None)
        if col_fecha:
            df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
        return df.dropna(how='all'), col_fecha
    except:
        return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    # Aplicar Filtro de Fecha
    df = df_raw.copy()
    if col_fecha_nombre:
        df = df[(df[col_fecha_nombre].dt.date >= fecha_inicio) & (df[col_fecha_nombre].dt.date <= fecha_fin)]

    # --- CUERPO PRINCIPAL ---
    st.title("🚀 Dashboard de Calidad Cenoa")
    st.info(f"📅 Período: {fecha_inicio.strftime('%d-%m-%Y')} al {fecha_fin.strftime('%d-%m-%Y')}")

    # Identificar columna NPS
    col_nps = next((c for c in df.columns if "escala" in c.lower() or "satisfecho" in c.lower()), None)
    
    if col_nps and len(df) > 0:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        total = len(df)
        promotores = len(df[df[col_nps] >= 9])
        detractores = len(df[df[col_nps] <= 6])
        nps_score = ((promotores - detractores) / total) * 100
        csat_score = df[col_nps].mean()

        # --- FILA 1: RELOJES (GAUGES) ---
        c1, c2 = st.columns(2)
        
        with c1:
            fig_nps = go.Figure(go.Indicator(
                mode = "gauge+number", value = nps_score, 
                title = {'text': "NPS (Net Promoter Score)"},
                gauge = {
                    'axis': {'range': [-100, 100]}, 
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [-100, 0], 'color': "#FF4B4B"},
                        {'range': [0, 70], 'color': "#FFA500"},
                        {'range': [70, 100], 'color': "#00CC96"}
                    ]
                }
            ))
            st.plotly_chart(fig_nps, use_container_width=True)
            
        with c2:
            fig_csat = go.Figure(go.Indicator(
                mode = "gauge+number", value = csat_score, 
                title = {'text': "CSAT (Satisfacción Media)"},
                gauge = {
                    'axis': {'range': [0, 10]}, 
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [0, 6], 'color': "#FF4B4B"},
                        {'range': [6, 8.5], 'color': "#FFA500"},
                        {'range': [8.5, 10], 'color': "#00CC96"}
                    ]
                }
            ))
            st.plotly_chart(fig_csat, use_container_width=True)

# --- SECCIÓN DE ANÁLISIS POR PILARES ---
        st.markdown("---")
        st.header("🔍 Análisis por Pilares de Calidad")
        cp1, cp2, cp3 = st.columns(3)

        # 1. Definimos las nuevas Claves para encontrar las columnas reales
        # Cambiamos 'solucionado' por 'chapa' para medir la reparación real
        col_reparacion = next((c for c in df.columns if "chapa" in c.lower() or "calidad" in c.lower()), None)
        col_tiempo = next((c for c in df.columns if "acordada" in c.lower() or "entrega" in c.lower()), None)
        col_atencion = next((c for c in df.columns if "explicaron" in c.lower() or "factura" in c.lower()), None)

        with cp1:
            st.subheader("🛠️ Calidad Reparación")
            if col_reparacion:
                # Como es escala 1-10, medimos cuántos pusieron 9 o 10
                df[col_reparacion] = pd.to_numeric(df[col_reparacion], errors='coerce')
                exitos = len(df[df[col_reparacion] >= 9])
                pct_rep = (exitos / total) * 100
                st.metric("Indice Chapa y Pintura", f"{int(pct_rep)}%")
                st.progress(pct_rep/100)
                st.caption("Clientes que calificaron con 9 o 10 la calidad del trabajo.")
            else:
                st.warning("No se halló la columna de 'Chapa y Pintura'")

        with cp2:
            st.subheader("⏰ Tiempo")
            # Este sigue buscando si se entregó en fecha (Sí/No)
            if col_tiempo:
                si_t = len(df[df[col_time_name].astype(str).str.lower().str.contains("sí|si")])
                pct_t = (si_t / total) * 100
                st.metric("Cumplimiento Entrega", f"{int(pct_t)}%")
                st.progress(pct_t/100)

        with cp3:
            st.subheader("📞 Atención")
            # Este busca si se explicó la factura (Sí/No)
            if col_atencion:
                si_a = len(df[df[col_fact_name].astype(str).str.lower().str.contains("sí|si")])
                pct_a = (si_a / total) * 100
                st.metric("Claridad en Factura", f"{int(pct_a)}%")
                st.progress(pct_a/100)

    else:
        st.warning("No hay datos suficientes para el rango de fechas seleccionado.")
else:
    st.error("No se pudo conectar con la fuente de datos.")
