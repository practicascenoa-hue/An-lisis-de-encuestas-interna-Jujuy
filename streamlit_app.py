import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Gestión de Calidad Cenoa", layout="wide")

# --- BARRA LATERAL (LADO IZQUIERDO) ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Google_Drive_icon_%282020%29.svg/512px-Google_Drive_icon_%282020%29.svg.png", width=50) # Puedes cambiar por logo Cenoa
st.sidebar.header("⚙️ Filtros de Control")

# 1. Selector de Rango de Fechas
st.sidebar.subheader("Calendario")
fecha_inicio = st.sidebar.date_input("Fecha Inicio", datetime(2024, 1, 1))
fecha_fin = st.sidebar.date_input("Fecha Fin", datetime.now())

st.sidebar.markdown("---")

# 2. Otros Selectores Sugeridos (Se llenan dinámicamente)
st.sidebar.subheader("Segmentación")

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Intentar convertir columna de fecha si existe
        col_fecha = next((c for c in df.columns if "fecha" in c.lower() or "marca temporal" in c.lower()), None)
        if col_fecha:
            df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
        return df.dropna(how='all'), col_fecha
    except: return None, None

df, col_fecha_nombre = load_data()

if df is not None:
    # --- APLICAR FILTRO DE FECHA ---
    if col_fecha_nombre:
        df = df[(df[col_fecha_nombre].dt.date >= fecha_inicio) & (df[col_fecha_nombre].dt.date <= fecha_fin)]

    # --- SELECTORES DINÁMICOS EN SIDEBAR ---
    # Buscamos columnas como "Sucursal" o "Asesor" para filtrar
    col_sucursal = next((c for c in df.columns if "sucursal" in c.lower() or "local" in c.lower()), None)
    if col_sucursal:
        sucursal_sel = st.sidebar.multiselect("Seleccionar Sucursal", options=df[col_sucursal].unique(), default=df[col_sucursal].unique())
        df = df[df[col_sucursal].isin(sucursal_sel)]

    # --- CUERPO PRINCIPAL ---
    st.title("📊 Portal de Calidad Cenoa")
    st.info(f"📅 Mostrando datos desde {fecha_inicio} hasta {fecha_fin}")

    # Lógica de NPS y CSAT (Igual que antes)
    col_nps = next((c for c in df.columns if "escala" in c.lower() or "satisfecho" in c.lower()), None)
    
    if col_nps and len(df) > 0:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        total = len(df)
        promotores = len(df[df[col_nps] >= 9])
        detractores = len(df[df[col_nps] <= 6])
        nps_score = ((promotores - detractores) / total) * 100
        csat_score = df[col_nps].mean()

        # --- RELOJES ---
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

        # --- PILARES DE PROCESO ---
        st.markdown("---")
        st.subheader("🛠️ Desempeño por Pilar de Servicio")
        pilares = {"FIR (Solución)": "solucionado", "Explicación": "explicaron", "Tiempo": "acordada", "Limpieza": "limpieza"}
        cols_p = st.columns(4)
        for i, (n, cl) in enumerate(pilares.items()):
            cp = next((c for c in df.columns if cl in c.lower()), None)
            if cp:
                si = len(df[df[cp].astype(str).str.lower().str.contains("sí|si")])
                p = (si/total)*100
                cols_p[i].metric(n, f"{int(p)}%")
                cols_p[i].progress(p/100)

    else:
        st.warning("No hay datos para el rango de fechas seleccionado.")
