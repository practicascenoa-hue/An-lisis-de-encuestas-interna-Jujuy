import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: BOTONES SLIM Y COLORES CORREGIDOS ---
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        height: 35px; /* Altura mínima */
        border-radius: 6px;
        border: none;
        color: white;
        font-weight: bold;
        font-size: 11px;
        text-transform: uppercase;
        margin-top: 0px;
    }
    /* Alineación de colores por columna */
    /* Columna 1 (Promotores/Excelente) -> VERDE */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div.stButton > button { background-color: #81C784; } 
    /* Columna 2 (Pasivos/Regular) -> AMARILLO */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div.stButton > button { background-color: #FFF176; color: #212529; } 
    /* Columna 3 (Detractores/Malo) -> ROJO */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div.stButton > button { background-color: #E57373; } 
    
    /* Espaciado para los captions */
    .stCaption { margin-bottom: -15px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        col_fecha = "Marca temporal"
        if col_fecha in df.columns:
            df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
        return df.dropna(how='all'), col_fecha
    except:
        return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("⚙️ Control")
    anio_sel = st.sidebar.selectbox("Año", sorted(df_raw['Año'].dropna().unique().astype(int), reverse=True))
    meses_nros = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].dropna().unique().astype(int))
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_nros])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # Mapeado de Columnas
    col_nps = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    col_csi = df.columns[19] 
    col_c_atencion = df.columns[8]; col_c_calidad = df.columns[12]; col_c_tiempo = df.columns[14]
    col_c_final = df.columns[17] 
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), None)
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), None)

    st.title("🚀 Dashboard de Calidad Cenoa")

    if len(df) > 0:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df[col_csi] = df[col_csi].astype(str).str.replace('%', '').str.replace(',', '.')
        df[col_csi] = pd.to_numeric(df[col_csi], errors='coerce')

        # NPS
        df_nps = df.dropna(subset=[col_nps])
        nps_reloj = df_nps[col_nps].mean() * 10 if not df_nps.empty else 0
        p_c = len(df[df[col_nps] >= 9]); d_c = len(df[df[col_nps] <= 6]); pas_c = len(df[(df[col_nps] > 6) & (df[col_nps] < 9)])

        # CSI
        df_csi_v = df.dropna(subset=[col_csi])
        csi_reloj = (df_csi_v[col_csi].mean() * 100 if df_csi_v[col_csi].max() <= 1.1 else df_csi_v[col_csi].mean()) if not df_csi_v.empty else 0
        exc_c = len(df[df[col_csi] >= (9 if csi_reloj < 15 else 90)])
        mal_c = len(df[df[col_csi] <= (6 if csi_reloj < 15 else 60)])
        reg_c = len(df) - exc_c - mal_c

        # --- RELOJES SLIM ---
        def crear_gauge_ultra_slim(valor, titulo):
            return go.Figure(go.Indicator(
                mode="gauge+number",
                value=valor,
                title={'text': titulo, 'font': {'size': 16, 'color': 'gray'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "lightgray"},
                    'bar': {'color': "#2c3e50", 'thickness': 0.15}, # Línea negra ultra fina
                    'bgcolor': "white",
                    'steps': [
                        {'range': [0, 59], 'color': "#FFCDD2"}, 
                        {'range': [60, 89], 'color': "#FFF9C4"}, 
                        {'range': [90, 100], 'color': "#C8E6C9"} 
                    ],
                    'threshold': {'line': {'color': "white", 'width': 0}, 'thickness': 0, 'value': valor}
                }
            )).update_layout(height=230, margin=dict(l=50, r=50, t=30, b=0))

        # --- LAYOUT PRINCIPAL ---
        col_reloj_1, col_reloj_2 = st.columns(2)
        
        with col_reloj_1:
            st.plotly_chart(crear_gauge_ultra_slim(nps_reloj, "NPS (Recomendación)"), use_container_width=True)
            st.caption("Filtrar auditoría NPS:")
            b_nps_1, b_nps_2, b_nps_3 = st.columns(3)
            if b_nps_1.button(f"PROMOTORES ({p_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Promotor"
            if b_nps_2.button(f"PASIVOS ({pas_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Pasivo"
            if b_nps_3.button(f"DETRACTORES ({d_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Detractor"

        with col_reloj_2:
            st.plotly_chart(crear_gauge_ultra_slim(csi_reloj, "CSI (Satisfacción)"), use_container_width=True)
            st.caption("Filtrar auditoría CSI:")
            b_csi_1, b_csi_2, b_csi_3 = st.columns(3)
            if b_csi_1.button(f"EXCELENTE ({exc_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Excelente"
            if b_csi_2.button(f"REGULAR ({reg_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Regular"
            if b_csi_3.button(f"MALO ({mal_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Malo"

        # --- TABLA ---
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.f_tipo:
            if st.session_state.f_tipo == "NPS":
                if st.session_state.f_val == "Promotor": df_f = df[df[col_nps] >= 9]
                elif st.session_state.f_val == "Detractor": df_f = df[df[col_nps] <= 6]
                else: df_f = df[(df[col_nps] > 6) & (df[col_nps] < 9)]
            else:
                lim = 9 if csi_reloj < 15 else 90
                lim_m = 6 if csi_reloj < 15 else 60
                if st.session_state.f_val == "Excelente": df_f = df[df[col_csi] >= lim]
                elif st.session_state.f_val == "Malo": df_f = df[df[col_csi] <= lim_m]
                else: df_f = df[(df[col_csi] > lim_m) & (df[col_csi] < lim)]

            cols_v = [col_cliente, col_asesor, col_csi, col_c_atencion, col_c_calidad, col_c_tiempo, col_c_final]
            cols_v = [c for c in cols_v if c in df.columns]
            st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
            st.dataframe(df_f.sort_values(by=col_csi, ascending=True)[cols_v], use_container_width=True)

    else: st.warning("Sin datos para este periodo.")
