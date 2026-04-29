import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        col_fecha = "Marca temporal"
        if col_fecha in df.columns:
            df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
            df = df.dropna(subset=[col_fecha])
        return df.dropna(how='all'), col_fecha
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    # --- PROCESAMIENTO DE FILTROS ---
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year.astype(int)
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month.astype(int)
    
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                  7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("⚙️ Filtros de Control")
    anios_disponibles = sorted(df_raw['Año'].unique().tolist(), reverse=True)
    anio_sel = st.sidebar.selectbox("Seleccione el Año", anios_disponibles)
    
    df_anio = df_raw[df_raw['Año'] == anio_sel]
    meses_en_anio = sorted(df_anio['Mes_Num'].unique().tolist())
    meses_nombres = [meses_dict[m] for m in meses_en_anio]
    mes_sel_nombre = st.sidebar.selectbox("Seleccione el Mes", meses_nombres)
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # --- CUERPO PRINCIPAL ---
    st.title("🚀 Dashboard de Calidad Cenoa")
    st.info(f"📅 Reporte: {mes_sel_nombre} {anio_sel}")

    # --- IDENTIFICACIÓN DE COLUMNAS CLAVE ---
    # NPS: Pregunta de recomendación
    col_nps_pregunta = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    
    # CSI: Calidad y Tiempo
    col_calidad = next((c for c in df.columns if "chapa" in c.lower() or "calidad del trabajo" in c.lower()), None)
    col_tiempo = next((c for c in df.columns if "acordada" in c.lower() or "tiempo de reparación" in c.lower()), None)
    
    if col_nps_pregunta and len(df) > 0:
        # 1. CÁLCULO NPS
        df[col_nps_pregunta] = pd.to_numeric(df[col_nps_pregunta], errors='coerce')
        df_nps = df.dropna(subset=[col_nps_pregunta])
        total_nps = len(df_nps)
        
        nps_score = 0
        if total_nps > 0:
            promotores = len(df_nps[df_nps[col_nps_pregunta] >= 9])
            detractores = len(df_nps[df_nps[col_nps_pregunta] <= 6])
            nps_score = ((promotores - detractores) / total_nps) * 100

        # 2. CÁLCULO CSI (Promedio Calidad + Tiempo)
        # Nota: Si Tiempo es Sí/No, lo convertimos (Sí=10, No=0) para promediar con la escala 1-10 de Calidad
        df['val_calidad'] = pd.to_numeric(df[col_calidad], errors='coerce') if col_calidad else None
        
        def convertir_tiempo(val):
            val_str = str(val).lower()
            if "si" in val_str or "sí" in val_str: return 10
            if "no" in val_str: return 0
            return pd.to_numeric(val, errors='coerce')

        df['val_tiempo'] = df[col_tiempo].apply(convertir_tiempo) if col_tiempo else None
        
        # Promediamos ambas columnas fila por fila y luego el total
        df['csi_row'] = df[['val_calidad', 'val_tiempo']].mean(axis=1)
        csi_total = df['csi_row'].mean()

        # --- RELOJES (GAUGES) ---
        c1, c2 = st.columns(2)
        with c1:
            fig_nps = go.Figure(go.Indicator(
                mode = "gauge+number", value = nps_score, title = {'text': "NPS Recomendación"},
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
            fig_csi = go.Figure(go.Indicator(
                mode = "gauge+number", value = csi_total, title = {'text': "CSI (Calidad + Tiempo)"},
                gauge = {
                    'axis': {'range': [0, 10]}, 
                    'bar': {'color': "black"},
                    'steps': [
                        {'range': [0, 7], 'color': "#FF4B4B"},
                        {'range': [7, 8.5], 'color': "#FFA500"},
                        {'range': [8.5, 10], 'color': "#00CC96"}
                    ]
                }
            ))
            st.plotly_chart(fig_csi, use_container_width=True)

        # --- PILARES DE APOYO ---
        st.markdown("---")
        cp1, cp2, cp3 = st.columns(3)
        with cp1:
            st.metric("Total Encuestas", total_nps)
        with cp2:
            val_c = df['val_calidad'].mean() if col_calidad else 0
            st.metric("Promedio Calidad", f"{val_c:.1f}/10")
        with cp3:
            val_t = df['val_tiempo'].mean() if col_tiempo else 0
            st.metric("Puntaje Tiempo", f"{val_t:.1f}/10")

    else:
        st.warning("No hay datos suficientes para calcular los indicadores este mes.")
else:
    st.error("Error al conectar con la base de datos.")
