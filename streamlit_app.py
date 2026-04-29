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
    anio_sel = st.sidebar.selectbox("Seleccione el Año", sorted(df_raw['Año'].unique(), reverse=True))
    meses_disp = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].unique())
    mes_sel_nombre = st.sidebar.selectbox("Seleccione el Mes", [meses_dict[m] for m in meses_disp])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # --- CUERPO PRINCIPAL ---
    st.title("🚀 Dashboard de Calidad Cenoa")
    st.info(f"📅 Reporte: {mes_sel_nombre} {anio_sel}")

    # Identificación de columnas
    col_nps_pregunta = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    col_comentarios = next((c for c in df.columns if "comentario" in c.lower() or "sugerencia" in c.lower() or "porque" in c.lower()), None)
    
    if col_nps_pregunta and len(df) > 0:
        df[col_nps_pregunta] = pd.to_numeric(df[col_nps_pregunta], errors='coerce')
        df = df.dropna(subset=[col_nps_pregunta])
        
        # Clasificación de Segmentos
        df['Segmento'] = df[col_nps_pregunta].apply(lambda x: 'Promotor' if x >= 9 else ('Detractor' if x <= 6 else 'Pasivo'))
        
        total = len(df)
        prom = df[df['Segmento'] == 'Promotor']
        det = df[df['Segmento'] == 'Detractor']
        pas = df[df['Segmento'] == 'Pasivo']
        
        nps_score = ((len(prom) - len(det)) / total) * 100

        # --- RELOJ NPS ---
        fig_nps = go.Figure(go.Indicator(
            mode = "gauge+number", value = nps_score, title = {'text': "NPS Global"},
            gauge = {'axis': {'range': [-100, 100]}, 'bar': {'color': "black"},
                     'steps': [{'range': [-100, 0], 'color': "#FF4B4B"},
                               {'range': 0, 70], 'color': "#FFA500"},
                               {'range': 70, 100], 'color': "#00CC96"}]}))
        st.plotly_chart(fig_nps, use_container_width=True)

        st.markdown("---")
        # --- BOTONES DE SEGMENTACIÓN (TABS) ---
        st.subheader("👥 Detalle por Segmento de Clientes")
        tab1, tab2, tab3 = st.tabs(["✅ Promotores (9-10)", "😐 Pasivos (7-8)", "❌ Detractores (0-6)"])

        with tab1:
            st.success(f"Se encontraron {len(prom)} Promotores")
            if not prom.empty:
                columnas_ver = [col_nps_pregunta, col_comentarios] if col_comentarios else [col_nps_pregunta]
                st.dataframe(prom[columnas_ver], use_container_width=True)
            else: st.write("No hay promotores en este periodo.")

        with tab2:
            st.warning(f"Se encontraron {len(pas)} Pasivos")
            if not pas.empty:
                columnas_ver = [col_nps_pregunta, col_comentarios] if col_comentarios else [col_nps_pregunta]
                st.dataframe(pas[columnas_ver], use_container_width=True)
            else: st.write("No hay clientes pasivos en este periodo.")

        with tab3:
            st.error(f"Se encontraron {len(det)} Detractores")
            if not det.empty:
                columnas_ver = [col_nps_pregunta, col_comentarios] if col_comentarios else [col_nps_pregunta]
                st.dataframe(det[columnas_ver], use_container_width=True)
            else: st.write("No hay detractores en este periodo.")

    else:
        st.warning("No hay datos suficientes para el periodo seleccionado.")
