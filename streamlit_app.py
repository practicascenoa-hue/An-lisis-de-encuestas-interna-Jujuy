import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="ENCUESTAS DE SATISFACCIÓN TALLER Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: CENTRADO DINÁMICO ---
st.markdown("""
    <style>
    /* Estilo de los botones */
    div.stButton > button {
        width: 100% !important;
        height: 34px !important;
        border-radius: 8px !important;
        border: 1px solid #dee2e6 !important;
        background-color: white !important;
        color: #495057 !important;
        font-size: 13px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    div.stButton > button:hover {
        border-color: #adb5bd !important;
        background-color: #f8f9fa !important;
    }

    /* FORZAR CENTRADO: 
       Aumentamos el margen izquierdo para desplazar el bloque de 3 botones a la derecha */
    [data-testid="column"] [data-testid="stHorizontalBlock"] {
        padding-left: 12% !important; /* Desplazamiento porcentual para mejor centrado */
        padding-right: 5% !important;
        gap: 10px !important;
    }

    /* Espaciado entre los botones individuales */
    [data-testid="column"] [data-testid="column"] {
        padding: 0px 4px !important;
    }

    /* Margen superior para separarlos del arco */
    div.stButton {
        margin-top: 20px;
    }
    
    .stPlotlyChart { margin-bottom: -30px; }
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
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df[col_csi] = df[col_csi].astype(str).str.replace('%', '').str.replace(',', '.')
        df[col_csi] = pd.to_numeric(df[col_csi], errors='coerce')

        nps_val = df[col_nps].mean() * 10 if not df.dropna(subset=[col_nps]).empty else 0
        csi_val = (df[col_csi].mean() * 100 if df[col_csi].max() <= 1.1 else df[col_csi].mean()) if not df.dropna(subset=[col_csi]).empty else 0
        
        p_c = len(df[df[col_nps] >= 9]); d_c = len(df[df[col_nps] <= 6]); pas_c = len(df[(df[col_nps] > 6) & (df[col_nps] < 9)])
        l_e = 9 if csi_val < 15 else 90; l_m = 6 if csi_val < 15 else 60
        exc_c = len(df[df[col_csi] >= l_e]); mal_c = len(df[df[col_csi] <= l_m]); reg_c = len(df) - exc_c - mal_c

        def crear_gauge(valor, titulo):
            return go.Figure(go.Indicator(
                mode="gauge+number", value=round(valor, 1),
                title={'text': f"<b>{titulo}</b>", 'font': {'size': 18}},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2c3e50", 'thickness': 0.15},
                       'steps': [{'range': [0, 59], 'color': "#EF9A9A"}, {'range': [60, 89], 'color': "#FFF59D"}, {'range': [90, 100], 'color': "#A5D6A7"}]}
            )).update_layout(height=230, margin=dict(l=60, r=60, t=60, b=0))

        # --- GRID DE CONTENIDO ---
        col_main_1, col_main_2 = st.columns(2)
        
        with col_main_1:
            st.plotly_chart(crear_gauge(nps_val, "NPS (Recomendación)"), use_container_width=True)
            bn1, bn2, bn3 = st.columns(3)
            bn1.button(f"🟢 {p_c} Prom", key="p1", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Promotor"}))
            bn2.button(f"🟡 {pas_c} Neu", key="p2", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo"}))
            bn3.button(f"🔴 {d_c} Det", key="p3", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Detractor"}))

        with col_main_2:
            st.plotly_chart(crear_gauge(csi_val, "CSI (Satisfacción)"), use_container_width=True)
            bc1, bc2, bc3 = st.columns(3)
            bc1.button(f"🟢 {exc_c} Exc", key="e1", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Excelente"}))
            bc2.button(f"🟡 {reg_c} Reg", key="e2", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Regular"}))
            bc3.button(f"🔴 {mal_c} Mal", key="e3", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Malo"}))

        # --- TABLA ---
        if st.session_state.f_tipo:
            st.markdown("---")
            l_e = 9 if csi_val < 15 else 90; l_m = 6 if csi_val < 15 else 60
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

    else: st.warning("Sin datos para este periodo.")
