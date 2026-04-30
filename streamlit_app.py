import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="ENCUESTAS DE SATISFACCIÓN TALLER Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS RADICAL: SIN SELECTORES DINÁMICOS ---
st.markdown("""
    <style>
    /* Forzamos que todos los botones de la app tengan texto blanco y sean visibles */
    .stButton > button {
        width: 100%;
        height: 40px;
        color: white !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        opacity: 1 !important;
    }
    
    /* VERDE: Promotores (n1) y Excelente (c1) */
    button[key="n1"], button[key="c1"] { background-color: #2E7D32 !important; }
    
    /* AMARILLO: Pasivos (n2) y Regular (c2) */
    button[key="n2"], button[key="c2"] { background-color: #FBC02D !important; color: #212529 !important; }
    
    /* ROJO: Detractores (n3) y Malo (c3) */
    button[key="n3"], button[key="c3"] { background-color: #D32F2F !important; }

    /* Ajuste de alineación para columnas de botones */
    [data-testid="column"] [data-testid="column"] {
        padding: 0px 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=30) # Reducido a 30s para refrescar más rápido
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
    # Sidebar
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("FILTROS PERIODO")
    anio_sel = st.sidebar.selectbox("Año", sorted(df_raw['Año'].dropna().unique().astype(int), reverse=True))
    meses_nros = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].dropna().unique().astype(int))
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_nros])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()
    col_nps = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    col_csi = df.columns[19] 

    st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")

    if len(df) > 0:
        # Limpieza rápida
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df[col_csi] = df[col_csi].astype(str).str.replace('%', '').str.replace(',', '.')
        df[col_csi] = pd.to_numeric(df[col_csi], errors='coerce')

        nps_val = df[col_nps].mean() * 10 if not df.dropna(subset=[col_nps]).empty else 0
        csi_val = (df[col_csi].mean() * 100 if df[col_csi].max() <= 1.1 else df[col_csi].mean()) if not df.dropna(subset=[col_csi]).empty else 0
        
        p_c = len(df[df[col_nps] >= 9]); d_c = len(df[df[col_nps] <= 6]); pas_c = len(df[(df[col_nps] > 6) & (df[col_nps] < 9)])
        exc_c = len(df[df[col_csi] >= (9 if csi_val < 15 else 90)])
        mal_c = len(df[df[col_csi] <= (6 if csi_val < 15 else 60)])
        reg_c = len(df) - exc_c - mal_c

        # Función de Reloj
        def crear_gauge(valor, titulo):
            return go.Figure(go.Indicator(
                mode="gauge+number", value=round(valor, 1),
                title={'text': f"<b>{titulo}</b>", 'font': {'size': 18}},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2c3e50", 'thickness': 0.15},
                       'steps': [{'range': [0, 59], 'color': "#EF9A9A"}, {'range': [60, 89], 'color': "#FFF59D"}, {'range': [90, 100], 'color': "#A5D6A7"}]}
            )).update_layout(height=230, margin=dict(l=50, r=50, t=60, b=0))

        # --- GRID DE CONTENIDO ---
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.plotly_chart(crear_gauge(nps_val, "NPS (Recomendación)"), use_container_width=True)
            st.markdown("<p style='text-align: center; font-size: 14px;'>Filtrar auditoría NPS:</p>", unsafe_allow_html=True)
            b_n1, b_n2, b_n3 = st.columns(3)
            with b_n1: st.button(f"PROMOTORES ({p_c})", key="n1", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Promotor"}))
            with b_n2: st.button(f"PASIVOS ({pas_c})", key="n2", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo"}))
            with b_n3: st.button(f"DETRACTORES ({d_c})", key="n3", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Detractor"}))

        with c_right:
            st.plotly_chart(crear_gauge(csi_val, "CSI (Satisfacción)"), use_container_width=True)
            st.markdown("<p style='text-align: center; font-size: 14px;'>Filtrar auditoría CSI:</p>", unsafe_allow_html=True)
            b_c1, b_c2, b_c3 = st.columns(3)
            with b_c1: st.button(f"EXCELENTE ({exc_c})", key="c1", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Excelente"}))
            with b_c2: st.button(f"REGULAR ({reg_c})", key="c2", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Regular"}))
            with b_c3: st.button(f"MALO ({mal_c})", key="c3", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Malo"}))

        # --- TABLA ---
        if st.session_state.f_tipo:
            st.markdown("---")
            l_e = 9 if csi_val < 15 else 90
            l_m = 6 if csi_val < 15 else 60
            if st.session_state.f_tipo == "NPS":
                if st.session_state.f_val == "Promotor": df_f = df[df[col_nps] >= 9]
                elif st.session_state.f_val == "Detractor": df_f = df[df[col_nps] <= 6]
                else: df_f = df[(df[col_nps] > 6) & (df[col_nps] < 9)]
            else:
                if st.session_state.f_val == "Excelente": df_f = df[df[col_csi] >= l_e]
                elif st.session_state.f_val == "Malo": df_f = df[df[col_csi] <= l_m]
                else: df_f = df[(df[col_csi] > l_m) & (df[col_csi] < l_e)]

            st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
            st.dataframe(df_f.sort_values(by=col_csi, ascending=True), use_container_width=True)

    else: st.warning("Sin datos.")
