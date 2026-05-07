import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re

# 1. Configuración de página
st.set_page_config(page_title="DASHBOARD POSTVENTA", layout="wide")

# Inicializar estados de sesión para filtros y botones
if "f_tipo" not in st.session_state:
    st.session_state.f_tipo = None
if "f_val" not in st.session_state:
    st.session_state.f_val = None
if "btn_active" not in st.session_state:
    st.session_state.btn_active = None
if "tab4_filter" not in st.session_state:
    st.session_state.tab4_filter = None

# --- CSS: ESTILO GLOBAL Y RESALTADO ---
st.markdown("""
    <style>
    div.stButton > button {
        width: 100% !important;
        height: 38px !important;
        border-radius: 8px !important;
    }
    button[kind="primary"] {
        background-color: #007bff !important;
        border-color: #007bff !important;
        color: white !important;
        font-weight: bold !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] { font-weight: bold; }
    
    /* ESTILO PARA TARJETAS DE LECTURA COMPLETA */
    .comentario-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #007bff;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .comentario-header {
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
        font-size: 14px;
    }
    .comentario-body {
        color: #555;
        font-size: 13px;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=30)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        col_fecha = "Marca temporal"
        if col_fecha in df.columns:
            df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
        return df.dropna(how='all'), col_fecha
    except: return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    # --- MAPEADO DE COLUMNAS ---
    col_comentario_K = df_raw.columns[10]
    col_ambiente_J = df_raw.columns[9]
    col_seguimiento = df_raw.columns[15]
    col_nps_puntaje = df_raw.columns[16]
    col_csi_final = df_raw.columns[18]
    col_nps_comentario = df_raw.columns[17]
    col_com_atencion = df_raw.columns[8]
    col_com_calidad = df_raw.columns[12]
    col_com_tiempo = df_raw.columns[14]
    col_t_concatenado = df_raw.columns[19]
    col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Cliente")
    col_asesor = next((c for c in df_raw.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")

    def clean_val(x):
        if pd.isna(x): return 0.0
        try:
            val = str(x).replace('%', '').replace(',', '.').strip()
            return float(val)
        except: return 0.0

    df_raw[col_nps_puntaje] = df_raw[col_nps_puntaje].apply(clean_val)
    df_raw[col_csi_final] = df_raw[col_csi_final].apply(clean_val)
    df_raw[col_ambiente_J] = df_raw[col_ambiente_J].apply(clean_val)

    # Sidebar: Filtros de Tiempo
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("FILTROS PERIODO")
    anio_sel = st.sidebar.selectbox("Año", sorted(df_raw['Año'].dropna().unique().astype(int), reverse=True))
    df_anio = df_raw[df_raw['Año'] == anio_sel].copy()
    
    meses_nros = sorted(df_anio['Mes_Num'].dropna().unique().astype(int))
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_nros])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    df_mes = df_anio[df_anio['Mes_Num'] == mes_sel_num].copy()

    st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 INDICADORES", "👤 ASESORES", "📊 EVOLUCIÓN MENSUAL", "⚠️ ANÁLISIS DE RECLAMOS"])

    with tab1:
        if len(df_mes) > 0:
            nps_val = df_mes[col_nps_puntaje].mean() * 10
            csi_raw = df_mes[col_csi_final].mean()
            csi_val = csi_raw * 100 if csi_raw <= 1.1 else csi_raw
            amb_val = df_mes[col_ambiente_J].mean() * 10
            c1, c2 = st.columns(2)
            def crear_gauge(valor, titulo):
                fig = go.Figure(go.Indicator(mode="gauge+number", value=valor, title={'text': f"<b>{titulo}</b>", 'font': {'size': 18}},
                    number={'valueformat': ".1f", 'suffix': "%", 'font': {'size': 40}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#34495e", 'thickness': 0.25},
                    'steps': [{'range': [0, 60], 'color': "#f8d7da"}, {'range': [60, 90], 'color': "#fff3cd"}, {'range': [90, 100], 'color': "#d1e7dd"}]}))
                fig.update_layout(height=280, margin=dict(l=30, r=30, t=80, b=20), paper_bgcolor='rgba(0,0,0,0)')
                return fig
            with c1:
                st.plotly_chart(crear_gauge(nps_val, "NPS"), use_container_width=True)
                p_c, d_c, pas_c = len(df_mes[df_mes[col_nps_puntaje] >= 9]), len(df_mes[df_mes[col_nps_puntaje] <= 6]), len(df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)])
                _, b1, b2, b3 = st.columns([0.1, 1, 1, 1])
                if b1.button(f"🟢 {p_c} Prom", key="btn1", type="primary" if st.session_state.btn_active == "btn1" else "secondary"):
                    st.session_state.update({"f_tipo":"NPS","f_val":"Promotor", "btn_active":"btn1"}); st.rerun()
                if b2.button(f"🟡 {pas_c} Neu", key="btn2", type="primary" if st.session_state.btn_active == "btn2" else "secondary"):
                    st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo", "btn_active":"btn2"}); st.rerun()
                if b3.button(f"🔴 {d_c} Det", key="btn3", type="primary" if st.session_state.btn_active == "btn3" else "secondary"):
