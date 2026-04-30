import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="ENCUESTAS DE SATISFACCIÓN TALLER Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: ESTILO DE BOTONES TIPO BADGE (Círculo + Texto) ---
st.markdown("""
    <style>
    /* Estilo base del botón: Blanco con borde gris suave */
    div.stButton > button {
        background-color: white !important;
        color: #555 !important;
        border: 1px solid #ddd !important;
        border-radius: 10px !important;
        height: 40px !important;
        width: 100% !important;
        font-weight: normal !important;
        text-transform: none !important;
        font-size: 14px !important;
    }
    
    /* Efecto Hover */
    div.stButton > button:hover {
        border-color: #aaa !important;
        background-color: #f9f9f9 !important;
    }

    /* Ajuste para los Relojes */
    .stPlotlyChart { margin-top: -20px; }
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
    except: return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("FILTROS PERIODO")
    anio_sel = st.sidebar.selectbox("Año", sorted(df_raw['Año'].dropna().unique().astype(int), reverse=True))
    meses_nros = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].dropna().unique().astype(int))
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_nros])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # Mapeado de Columnas
    col_nps = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    col_csi = df.columns[19] 

    st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")

    if len(df) > 0:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df[col_csi] = df[col_csi].astype(str).str.replace('%', '').str.replace(',', '.')
        df[col_csi] = pd.to_numeric(df[col_csi], errors='coerce')

        nps_val = df[col_nps].mean() * 10 if not df.dropna(subset=[col_nps]).empty else 0
        csi_val = (df[col_csi].mean() * 100 if df[col_csi].max() <= 1.1 else df[col_csi].mean()) if not df.dropna(subset=[col_csi]).empty else 0
        
        # Conteos
        p_c = len(df[df[col_nps] >= 9]); d_c = len(df[df[col_nps] <= 6]); pas_c = len(df[(df[col_nps] > 6) & (df[col_nps] < 9)])
        l_e = 9 if csi_val < 15 else 90; l_m = 6 if csi_val < 15 else 60
        exc_c = len(df[df[col_csi] >= l_e]); mal_c = len(df[df[col_csi] <= l_m]); reg_c = len(df) - exc_c - mal_c

        # Función de Reloj
        def crear_gauge(valor, titulo):
            return go.Figure(go.Indicator(
                mode="gauge+number", value=round(valor, 1),
                title={'text': f"<b>{titulo}</b>", 'font': {'size': 18}},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2c3e50", 'thickness': 0.15},
                       'steps': [{'range': [0, 59], 'color': "#EF9A9A"}, {'range': [60, 89], 'color': "#FFF59D"}, {'range': [90, 100], 'color': "#A5D6A7"}]}
            )).update_layout(height=230, margin=dict(l=50, r=50, t=60, b=0))

        # --- LAYOUT PRINCIPAL ---
        col_main_1, col_main_2 = st.columns(2)
        
        with col_main_1:
            st.plotly_chart(crear_gauge(nps_val, "NPS (Recomendación)"), use_container_width=True)
            st.markdown("<p style='text-align: center; font-size: 13px; color: #666;'>Filtrar auditoría NPS:</p>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            # Botones con el punto de color (Emoji)
            with b1: 
                if st.button(f"🟢 {p_c} Prom", key="btn_prom"): 
                    st.session_state.f_tipo, st.session_state.f_val = "NPS", "Promotor"
            with b2: 
                if st.button(f"🟡 {pas_c} Neu", key="btn_neu"): 
                    st.session_state.f_tipo, st.session_state.f_val = "NPS", "Pasivo"
            with b3: 
                if st.button(f"🔴 {d_c} Det", key="btn_det"): 
                    st.session_state.f_tipo, st.session_state.f_val = "NPS", "Detractor"

        with col_main_2:
            st.plotly_chart(crear_gauge(csi_val, "CSI (Satisfacción)"), use_container_width=True)
            st.markdown("<p style='text-align: center; font-size: 13px; color: #666;'>Filtrar auditoría CSI:</p>", unsafe_allow_html=True)
            bc1, bc2, bc3 = st.columns(3)
            with bc1: 
                if st.button(f"🟢 {exc_c} Exc", key="btn_exc"): 
                    st.session_state.f_tipo, st.session_state.f_val = "CSI", "Excelente"
            with bc2: 
                if st.button(f"🟡 {reg_c} Reg", key="btn_reg"): 
                    st.session_state.f_tipo, st.session_state.f_val = "CSI", "Regular"
            with bc3: 
                if st.button(f"🔴 {mal_c} Mal", key="btn_mal"): 
                    st.session_state.f_tipo, st.session_state.f_val = "CSI", "Malo"

        # --- TABLA DE AUDITORÍA ---
        if st.session_state.f_tipo:
            st.markdown("---")
            if st.session_state.f_tipo == "NPS":
                if st.session_state.f_val == "Promotor": df_f = df[df[col_nps] >= 9]
                elif st.session_state.f_val == "Detractor": df_f = df[df[col_nps] <= 6]
                else: df_f = df[(df[col_nps] > 6) & (df[col_nps] < 9)]
            else:
                l_e = 9 if csi_val < 15 else 90; l_m = 6 if csi_val < 15 else 60
                if st.session_state.f_val == "Excelente": df_f = df[df[col_csi] >= l_e]
                elif st.session_state.f_val == "Malo": df_f = df[df[col_csi] <= l_m]
                else: df_f = df[(df[col_csi] > l_m) & (df[col_csi] < l_e)]

            st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
            st.dataframe(df_f.sort_values(by=col_csi, ascending=True), use_container_width=True)

    else: st.warning("Sin datos para este periodo.")
