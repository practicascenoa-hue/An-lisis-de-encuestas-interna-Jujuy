import streamlit as st
import pandas as pd

# 1. Configuración de página
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: BOTONES SLIM Y COLORES FUERTES ---
st.markdown("""
    <style>
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
    /* Columna 1: Verde | Columna 2: Amarillo | Columna 3: Rojo */
    [data-testid="stHorizontalBlock"] div:nth-child(1) button { background-color: #2E7D32 !important; }
    [data-testid="stHorizontalBlock"] div:nth-child(2) button { background-color: #FBC02D !important; color: #212529 !important; }
    [data-testid="stHorizontalBlock"] div:nth-child(3) button { background-color: #D32F2F !important; }
    
    /* Estilo para las métricas */
    [data-testid="stMetricValue"] { font-size: 48px; font-weight: bold; color: #1E88E5; }
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
    col_csi = df.columns[19] # Columna T
    col_c_atencion = df.columns[8]; col_c_calidad = df.columns[12]; col_c_tiempo = df.columns[14]
    col_c_final = df.columns[17] # Columna R
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), None)
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), None)

    st.title("🚀 Dashboard de Calidad Cenoa")

    if len(df) > 0:
        # Limpieza
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df[col_csi] = df[col_csi].astype(str).str.replace('%', '').str.replace(',', '.')
        df[col_csi] = pd.to_numeric(df[col_csi], errors='coerce')

        # Cálculos
        nps_avg = df[col_nps].mean() * 10 if not df[col_nps].isna().all() else 0.0
        csi_avg = (df[col_csi].mean() * 100 if df[col_csi].max() <= 1.1 else df[col_csi].mean()) if not df[col_csi].isna().all() else 0.0
        
        p_c = len(df[df[col_nps] >= 9]); d_c = len(df[df[col_nps] <= 6]); pas_c = len(df[(df[col_nps] > 6) & (df[col_nps] < 9)])
        lim_e = 90 if csi_avg > 11 else 9
        lim_m = 60 if csi_avg > 11 else 6
        exc_c = len(df[df[col_csi] >= lim_e]); mal_c = len(df[df[col_csi] <= lim_m]); reg_c = len(df) - exc_c - mal_c

        # --- INDICADORES (MÉTRICAS ESTABLES) ---
        c1, c2 = st.columns(2)
        with c1:
            st.metric("NPS (Recomendación)", f"{nps_avg:.1f} / 100")
            st.write("---")
            cn1, cn2, cn3 = st.columns(3)
            if cn1.button(f"PROMOTORES ({p_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Promotor"
            if cn2.button(f"PASIVOS ({pas_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Pasivo"
            if cn3.button(f"DETRACTORES ({d_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Detractor"

        with c2:
            st.metric("CSI (Satisfacción)", f"{csi_avg:.1f} / 100")
            st.write("---")
            cc1, cc2, cc3 = st.columns(3)
            if cc1.button(f"EXCELENTE ({exc_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Excelente"
            if cc2.button(f"REGULAR ({reg_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Regular"
            if cc3.button(f"MALO ({mal_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Malo"

        # --- TABLA ---
        if st.session_state.f_tipo:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.session_state.f_tipo == "NPS":
                if st.session_state.f_val == "Promotor": df_f = df[df[col_nps] >= 9]
                elif st.session_state.f_val == "Detractor": df_f = df[df[col_nps] <= 6]
                else: df_f = df[(df[col_nps] > 6) & (df[col_nps] < 9)]
            else:
                if st.session_state.f_val == "Excelente": df_f = df[df[col_csi] >= lim_e]
                elif st.session_state.f_val == "Malo": df_f = df[df[col_csi] <= lim_m]
                else: df_f = df[(df[col_csi] > lim_m) & (df[col_csi] < lim_e)]

            cols = [c for c in [col_cliente, col_asesor, col_csi, col_c_atencion, col_c_calidad, col_c_tiempo, col_c_final] if c in df.columns]
            st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
            st.dataframe(df_f.sort_values(by=col_csi, ascending=True)[cols], use_container_width=True)
    else:
        st.info("No hay datos para este periodo.")
else:
    st.error("Error al cargar el Excel.")
