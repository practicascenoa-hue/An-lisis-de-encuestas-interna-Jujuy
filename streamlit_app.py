import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de página y Estilo Visual
st.set_page_config(page_title="ENCUESTAS SATISFACCIÓN TALLER Cenoa", layout="wide")

# CSS para botones con colores semafóricos reales y diseño de tarjetas
st.markdown("""
    <style>
    div.stButton > button {
        width: 80%;
        height: 80px;
        border-radius: 15px;
        border: none;
        color: white;
        font-weight: bold;
        font-size: 18px;
        transition: 0.3s;
    }
    .stColumn:nth-of-type(1) div.stButton > button { background-color: #28a745; } 
    .stColumn:nth-of-type(2) div.stButton > button { background-color: #ffc107; color: #212529; } 
    .stColumn:nth-of-type(3) div.stButton > button { background-color: #dc3545; } 
    
    div.stButton > button:hover {
        opacity: 0.8;
        transform: scale(1.02);
    }
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
    # Preparación de filtros
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year.astype(int)
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month.astype(int)
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                  7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("SELECCIONAR AÑO Y MES:")
    anio_sel = st.sidebar.selectbox("Año", sorted(df_raw['Año'].unique(), reverse=True))
    meses_disp = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].unique())
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_disp])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # --- IDENTIFICACIÓN DE COLUMNAS POR NOMBRE O POSICIÓN ---
    col_nps_interna = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), None)
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), None)
    
    # AJUSTE: Seleccionamos la columna 18 (Índice 17 en Python)
    col_comentarios_exp = df.columns[17] if len(df.columns) > 17 else None

    st.title("ENCUESTAS SATISFACCIÓN TALLER Cenoa")

    if col_nps_interna and len(df) > 0:
        df[col_nps_interna] = pd.to_numeric(df[col_nps_interna], errors='coerce')
        df = df.dropna(subset=[col_nps_interna])
        
        # Segmentación
        total = len(df)
        df['Segmento'] = df[col_nps_interna].apply(lambda x: 'Promotor' if x >= 9 else ('Detractor' if x <= 6 else 'Pasivo'))
        prom = df[df['Segmento'] == 'Promotor']
        pas = df[df['Segmento'] == 'Pasivo']
        det = df[df['Segmento'] == 'Detractor']
        nps_score = ((len(prom) - len(det)) / total) * 100

        # --- RELOJES ---
        c1, c2 = st.columns(2)
        with c1:
            fig_nps = go.Figure(go.Indicator(
                mode="gauge+number", value=nps_score, title={'text': "NPS Recomendación"},
                gauge={'axis': {'range': [-100, 100]}, 'bar': {'color': "black"},
                       'steps': [
                           {'range': [-100, 0], 'color': "#FF4B4B"},
                           {'range': [0, 70], 'color': "#FFA500"},
                           {'range': [70, 100], 'color': "#00CC96"}
                       ]}
            ))
            st.plotly_chart(fig_nps, use_container_width=True)
            
            # --- BOTONES CORRECTOS ---
            st.write("### Auditoría de Comentarios:")
            if "filtro_nps" not in st.session_state: st.session_state.filtro_nps = None
            
            col_b1, col_b2, col_b3 = st.columns(3)
            if col_b1.button(f"PROMOTORES\n({len(prom)})"): st.session_state.filtro_nps = "Promotor"
            if col_b2.button(f"PASIVOS\n({len(pas)})"): st.session_state.filtro_nps = "Pasivo"
            if col_b3.button(f"DETRACTORES\n({len(det)})"): st.session_state.filtro_nps = "Detractor"

        with c2:
            csi_score = 0
            col_csi_calidad = next((c for c in df.columns if "calidad" in c.lower()), None)
            if col_csi_calidad:
                csi_score = pd.to_numeric(df[col_csi_calidad], errors='coerce').mean() * 10

            fig_csi = go.Figure(go.Indicator(
                mode="gauge+number", value=csi_score if not pd.isna(csi_score) else 0, title={'text': "Índice de Calidad"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "black"},
                       'steps': [
                           {'range': [0, 70], 'color': "#FF4B4B"},
                           {'range': [70, 85], 'color': "#FFA500"},
                           {'range': [85, 100], 'color': "#00CC96"}
                       ]}
            ))
            st.plotly_chart(fig_csi, use_container_width=True)

        # --- TABLA DETALLADA ---
        st.markdown("---")
        if st.session_state.filtro_nps:
            df_auditoria = df[df['Segmento'] == st.session_state.filtro_nps]
            
            # Armamos las columnas finales
            cols_finales = []
            if col_cliente: cols_finales.append(col_cliente)
            if col_asesor: cols_finales.append(col_asesor)
            if col_comentarios_exp: cols_finales.append(col_comentarios_exp)
            
            st.subheader(f"Comentarios de {st.session_state.filtro_nps}s")
            st.dataframe(df_auditoria[cols_finales], use_container_width=True)
        else:
            st.info("💡 Selecciona un botón arriba para ver los nombres y comentarios.")

    else: st.warning("Sin datos para este mes.")
else: st.error("Error al cargar Google Sheets.")
