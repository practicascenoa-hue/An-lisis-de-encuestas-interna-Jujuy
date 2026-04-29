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

    # --- IDENTIFICACIÓN DE COLUMNAS ---
    col_nps_preg = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    col_calidad = next((c for c in df.columns if "chapa" in c.lower() or "calidad del trabajo" in c.lower()), None)
    col_tiempo = next((c for c in df.columns if "acordada" in c.lower() or "tiempo de reparación" in c.lower()), None)
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), None)
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), None)
    col_coment = next((c for c in df.columns if "porque" in c.lower() or "comentario" in c.lower() or "sugerencia" in c.lower()), None)

    st.title("🚀 Dashboard de Calidad Cenoa")
    st.info(f"📅 Reporte: {mes_sel_nombre} {anio_sel}")

    if col_nps_preg and len(df) > 0:
        df[col_nps_preg] = pd.to_numeric(df[col_nps_preg], errors='coerce')
        df = df.dropna(subset=[col_nps_preg])
        
        # Segmentación
        total = len(df)
        df['Segmento'] = df[col_nps_preg].apply(lambda x: 'Promotor' if x >= 9 else ('Detractor' if x <= 6 else 'Pasivo'))
        
        promotores = df[df['Segmento'] == 'Promotor']
        pasivos = df[df['Segmento'] == 'Pasivo']
        detractores = df[df['Segmento'] == 'Detractor']
        
        nps_score = ((len(promotores) - len(detractores)) / total) * 100

        # CSI Score (Calidad + Tiempo)
        df['v_calidad'] = pd.to_numeric(df[col_calidad], errors='coerce') if col_calidad else 0
        def conv_t(v):
            v_s = str(v).lower()
            return 10 if "si" in v_s or "sí" in v_s else (0 if "no" in v_s else pd.to_numeric(v, errors='coerce'))
        df['v_tiempo'] = df[col_tiempo].apply(conv_t) if col_tiempo else 0
        csi_score = df[['v_calidad', 'v_tiempo']].mean(axis=1).mean()

        # --- FILA 1: RELOJES (ESTRUCTURA CORREGIDA) ---
        c1, c2 = st.columns(2)
        with c1:
            fig_nps = go.Figure(go.Indicator(
                mode = "gauge+number", 
                value = nps_score, 
                title = {'text': "NPS Recomendación"},
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
            
            # --- BOTONES DE FILTRO ---
            st.write("🔍 **Ver listado de:**")
            if "filtro_activo" not in st.session_state:
                st.session_state.filtro_activo = None

            b1, b2, b3 = st.columns(3)
            if b1.button(f"🟢 {len(promotores)} Prom"):
                st.session_state.filtro_activo = "Promotor"
            if b2.button(f"🟡 {len(pasivos)} Neu"):
                st.session_state.filtro_activo = "Pasivo"
            if b3.button(f"🔴 {len(detractores)} Det"):
                st.session_state.filtro_activo = "Detractor"

        with c2:
            fig_csi = go.Figure(go.Indicator(
                mode = "gauge+number", 
                value = csi_score, 
                title = {'text': "CSI (Calidad + Tiempo)"},
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

        # --- MOSTRAR DATOS ---
        st.markdown("---")
        cols_finales = [c for c in [col_cliente, col_asesor, col_nps_preg, col_coment] if c is not None]

        if st.session_state.filtro_activo == "Promotor":
            st.success(f"Mostrando {len(promotores)} Promotores")
            st.dataframe(promotores[cols_finales], use_container_width=True)
        elif st.session_state.filtro_activo == "Pasivo":
            st.warning(f"Mostrando {len(pasivos)} Pasivos/Neutrales")
            st.dataframe(pasivos[cols_finales], use_container_width=True)
        elif st.session_state.filtro_activo == "Detractor":
            st.error(f"Mostrando {len(detractores)} Detractores")
            st.dataframe(detractores[cols_finales], use_container_width=True)
        else:
            st.info("Haz clic en los botones (Prom, Neu o Det) para ver los comentarios de los clientes.")

    else:
        st.warning("No hay suficientes datos para este mes.")
else:
    st.error("No se pudo conectar con el Google Sheet.")
