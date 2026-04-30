import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="ENCUESTAS DE SATISFACCIÓN TALLER Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: CORRECCIÓN DE ALINEACIÓN Y COLORES POR TEXTO ---
st.markdown("""
    <style>
    /* Estilo base para todos los botones */
    div.stButton > button {
        width: 100%;
        height: 35px;
        border-radius: 6px;
        border: none;
        color: white !important;
        font-weight: bold;
        font-size: 11px;
        text-transform: uppercase;
    }

    /* COLORES ESPECÍFICOS POR CONTENIDO (Selección por texto) */
    /* Verdes */
    div.stButton > button:has(div:contains("PROMOTORES")),
    div.stButton > button:has(div:contains("EXCELENTE")) {
        background-color: #2E7D32 !important;
    }
    
    /* Amarillos */
    div.stButton > button:has(div:contains("PASIVOS")),
    div.stButton > button:has(div:contains("REGULAR")) {
        background-color: #FBC02D !important;
        color: #212529 !important;
    }
    
    /* Rojos */
    div.stButton > button:has(div:contains("DETRACTORES")),
    div.stButton > button:has(div:contains("MALO")) {
        background-color: #D32F2F !important;
    }
    
    /* Ajuste de márgenes para que no se desplacen */
    [data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    
    .stPlotlyChart { margin-top: -10px; }
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
    
    st.sidebar.header("FILTROS PERIODO")
    anios_disp = sorted(df_raw['Año'].dropna().unique().astype(int), reverse=True)
    anio_sel = st.sidebar.selectbox("Año", anios_disp)
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

    st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")

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
                value=round(valor, 1),
                title={'text': f"<b>{titulo}</b>", 'font': {'size': 18, 'color': '#333'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "lightgray"},
                    'bar': {'color': "#2c3e50", 'thickness': 0.15},
                    'bgcolor': "white",
                    'steps': [
                        {'range': [0, 59], 'color': "#EF9A9A"}, 
                        {'range': [60, 89], 'color': "#FFF59D"}, 
                        {'range': [90, 100], 'color': "#A5D6A7"} 
                    ]
                }
            )).update_layout(height=230, margin=dict(l=50, r=50, t=60, b=0))

        # --- LAYOUT PRINCIPAL ---
        col_main_1, col_main_2 = st.columns(2)
        
        with col_main_1:
            st.plotly_chart(crear_gauge_ultra_slim(nps_reloj, "NPS (Recomendación)"), use_container_width=True)
            st.caption("Filtrar auditoría NPS:")
            b_n1, b_n2, b_n3 = st.columns(3)
            with b_n1: st.button(f"PROMOTORES ({p_c})", on_click=lambda: st.session_state.update({"f_tipo": "NPS", "f_val": "Promotor"}))
            with b_n2: st.button(f"PASIVOS ({pas_c})", on_click=lambda: st.session_state.update({"f_tipo": "NPS", "f_val": "Pasivo"}))
            with b_n3: st.button(f"DETRACTORES ({d_c})", on_click=lambda: st.session_state.update({"f_tipo": "NPS", "f_val": "Detractor"}))

        with col_main_2:
            st.plotly_chart(crear_gauge_ultra_slim(csi_reloj, "CSI (Satisfacción)"), use_container_width=True)
            st.caption("Filtrar auditoría CSI:")
            b_c1, b_c2, b_c3 = st.columns(3)
            with b_c1: st.button(f"EXCELENTE ({exc_c})", on_click=lambda: st.session_state.update({"f_tipo": "CSI", "f_val": "Excelente"}))
            with b_c2: st.button(f"REGULAR ({reg_c})", on_click=lambda: st.session_state.update({"f_tipo": "CSI", "f_val": "Regular"}))
            with b_c3: st.button(f"MALO ({mal_c})", on_click=lambda: st.session_state.update({"f_tipo": "CSI", "f_val": "Malo"}))

        # --- TABLA ---
        if st.session_state.f_tipo:
            st.markdown("---")
            if st.session_state.f_tipo == "NPS":
                if st.session_state.f_val == "Promotor": df_f = df[df[col_nps] >= 9]
                elif st.session_state.f_val == "Detractor": df_f = df[df[col_nps] <= 6]
                else: df_f = df[(df[col_nps] > 6) & (df[col_nps] < 9)]
            else:
                l_e = 9 if csi_reloj < 15 else 90
                l_m = 6 if csi_reloj < 15 else 60
                if st.session_state.f_val == "Excelente": df_f = df[df[col_csi] >= l_e]
                elif st.session_state.f_val == "Malo": df_f = df[df[col_csi] <= l_m]
                else: df_f = df[(df[col_csi] > l_m) & (df[col_csi] < l_e)]

            cols_v = [col_cliente, col_asesor, col_csi, col_c_atencion, col_c_calidad, col_c_tiempo, col_c_final]
            cols_v = [c for c in cols_v if c in df.columns]
            st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
            st.dataframe(df_f.sort_values(by=col_csi, ascending=True)[cols_v], use_container_width=True)

    else: st.warning("Sin datos para este periodo.")
