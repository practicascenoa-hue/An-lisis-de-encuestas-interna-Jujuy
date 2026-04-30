import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de página y Estilo Visual
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# CSS para botones con colores semafóricos reales
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        height: 85px;
        border-radius: 12px;
        border: none;
        color: white;
        font-weight: bold;
        font-size: 16px;
        transition: 0.3s;
    }
    .stColumn:nth-of-type(1) div.stButton > button { background-color: #28a745; } 
    .stColumn:nth-of-type(2) div.stButton > button { background-color: #ffc107; color: #212529; } 
    .stColumn:nth-of-type(3) div.stButton > button { background-color: #dc3545; } 
    div.stButton > button:hover { opacity: 0.8; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

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
    except:
        return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    # Preparación de filtros temporales
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year.astype(int)
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month.astype(int)
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                  7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("⚙️ Control de Reporte")
    anio_sel = st.sidebar.selectbox("Año", sorted(df_raw['Año'].unique(), reverse=True))
    meses_disp = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].unique())
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_disp])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # --- IDENTIFICACIÓN DE COLUMNAS ---
    col_nps_interna = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    
    # NUEVO: Referencia directa a la columna T (índice 19 en Python) para el CSI
    col_csi_t = df.columns[19] if len(df.columns) > 19 else None
    
    # Atributos individuales (H, L, N)
    col_atencion_h = df.columns[7] 
    col_calidad_l = df.columns[11]  
    col_tiempo_n = df.columns[13]   
    
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), None)
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), None)
    col_comentarios_exp = df.columns[17] # Columna 18

    st.title("🚀 Dashboard de Calidad Cenoa")

    if col_nps_interna and col_csi_t and len(df) > 0:
        # Limpieza de datos
        df[col_nps_interna] = pd.to_numeric(df[col_nps_interna], errors='coerce')
        df[col_csi_t] = pd.to_numeric(df[col_csi_t], errors='coerce')
        df = df.dropna(subset=[col_nps_interna, col_csi_t])
        
        # Lógica NPS
        df['Seg_NPS'] = df[col_nps_interna].apply(lambda x: 'Promotor' if x >= 9 else ('Detractor' if x <= 6 else 'Pasivo'))
        nps_score = ((len(df[df['Seg_NPS']=='Promotor']) - len(df[df['Seg_NPS']=='Detractor'])) / len(df)) * 100

        # Lógica CSI Directa de Columna T
        csi_global = df[col_csi_t].mean() * 100 if df[col_csi_t].max() <= 1 else df[col_csi_t].mean()
        df['Seg_CSI'] = df[col_csi_t].apply(lambda x: 'Excelente' if x >= 9 else ('Malo' if x <= 6 else 'Regular'))

        # --- VISUALIZACIÓN ---
        if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
        if "f_val" not in st.session_state: st.session_state.f_val = None

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(go.Figure(go.Indicator(
                mode="gauge+number", value=nps_score, title={'text': "NPS Recomendación"},
                gauge={'axis': {'range': [-100, 100]}, 'bar': {'color': "black"},
                       'steps': [{'range': [-100, 0], 'color': "#FF4B4B"},
                                 {'range': [0, 70], 'color': "#FFA500"},
                                 {'range': [70, 100], 'color': "#00CC96"}]})), use_container_width=True)
            
            st.write("🔍 **Auditar por Recomendación:**")
            b1, b2, b3 = st.columns(3)
            if b1.button(f"PROMOTORES\n({len(df[df['Seg_NPS']=='Promotor'])})"): 
                st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Promotor"
            if b2.button(f"PASIVOS\n({len(df[df['Seg_NPS']=='Pasivo'])})"): 
                st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Pasivo"
            if b3.button(f"DETRACTORES\n({len(df[df['Seg_NPS']=='Detractor'])})"): 
                st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Detractor"

        with c2:
            st.plotly_chart(go.Figure(go.Indicator(
                mode="gauge+number", value=csi_global, title={'text': "CSI Unificado (Columna T)"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "black"},
                       'steps': [{'range': [0, 70], 'color': "#FF4B4B"},
                                 {'range': [70, 85], 'color': "#FFA500"},
                                 {'range': [85, 100], 'color': "#00CC96"}]})), use_container_width=True)
            
            st.write("🔍 **Auditar por CSI (Satisfacción de Servicio):**")
            bc1, bc2, bc3 = st.columns(3)
            if bc1.button(f"EXCELENTE\n({len(df[df['Seg_CSI']=='Excelente'])})"): 
                st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Excelente"
            if bc2.button(f"REGULAR\n({len(df[df['Seg_CSI']=='Regular'])})"): 
                st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Regular"
            if bc3.button(f"MALO\n({len(df[df['Seg_CSI']=='Malo'])})"): 
                st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Malo"

        # --- TABLA DE AUDITORÍA ---
        st.markdown("---")
        if st.session_state.f_tipo:
            st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
            col_target = 'Seg_NPS' if st.session_state.f_tipo == "NPS" else 'Seg_CSI'
            df_final = df[df[col_target] == st.session_state.f_val].copy()
            
            cols_show = [c for c in [col_cliente, col_asesor, col_atencion_h, col_calidad_l, col_tiempo_n, col_comentarios_exp] if c]
            st.dataframe(df_final[cols_show], use_container_width=True)
        else:
            st.info("💡 Selecciona un botón arriba para analizar los comentarios de los clientes.")

    else: st.warning("Sin datos para este periodo o falta columna T en el sheet.")
else: st.error("No se pudo conectar con la base de datos.")
