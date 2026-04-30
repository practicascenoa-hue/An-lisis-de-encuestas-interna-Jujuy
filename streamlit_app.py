import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: BOTONES COMPACTOS ---
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        height: 45px;
        border-radius: 8px;
        border: none;
        color: white;
        font-weight: bold;
        font-size: 13px;
        text-transform: uppercase;
    }
    .stColumn:nth-of-type(1) div.stButton > button { background-color: #81C784; } /* Verde Suave */
    .stColumn:nth-of-type(2) div.stButton > button { background-color: #FFF176; color: #212529; } /* Amarillo Suave */
    .stColumn:nth-of-type(3) div.stButton > button { background-color: #E57373; } /* Rojo Suave */
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
    # Filtros de Fecha
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
    col_c_final = df.columns[17] 
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), None)
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), None)

    st.title("🚀 Dashboard de Calidad Cenoa")

    if len(df) > 0:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df[col_csi] = df[col_csi].astype(str).str.replace('%', '').str.replace(',', '.')
        df[col_csi] = pd.to_numeric(df[col_csi], errors='coerce')

        # NPS Logic (Mapeo a escala 0-100 para el reloj según tu criterio)
        df_nps = df.dropna(subset=[col_nps])
        # Nota: NPS tradicional es (P-D), pero para el reloj 0-100 usamos el promedio de recomendación
        score_nps_reloj = df_nps[col_nps].mean() * 10 
        
        p_c = len(df[df[col_nps] >= 9])
        d_c = len(df[df[col_nps] <= 6])
        pas_c = len(df[(df[col_nps] > 6) & (df[col_nps] < 9)])

        # CSI Logic
        df_csi_v = df.dropna(subset=[col_csi])
        csi_reloj = df_csi_v[col_csi].mean() * 100 if df_csi_v[col_csi].max() <= 1.1 else df_csi_v[col_csi].mean()
        
        exc_c = len(df[df[col_csi] >= 90]) if csi_reloj > 10 else len(df[df[col_csi] >= 9])
        mal_c = len(df[df[col_csi] <= 60]) if csi_reloj > 10 else len(df[df[col_csi] <= 6])
        reg_c = len(df) - exc_c - mal_c

        # --- RELOJES ESTILIZADOS ---
        def crear_gauge(valor, titulo):
            return go.Figure(go.Indicator(
                mode="gauge+number",
                value=valor,
                title={'text': titulo, 'font': {'size': 18}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
                    'bar': {'color': "#2c3e50", 'thickness': 0.5}, # Barra indicadora fina
                    'bgcolor': "white",
                    'borderwidth': 0,
                    'shape': "angular",
                    'steps': [
                        {'range': [0, 59], 'color': "#FFCDD2"}, # Rojo suave
                        {'range': [60, 89], 'color': "#FFF9C4"}, # Amarillo suave
                        {'range': [90, 100], 'color': "#C8E6C9"} # Verde suave
                    ],
                }
            )).update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20))

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(crear_gauge(score_nps_reloj, "NPS (Recomendación)"), use_container_width=True)
            st.caption("Filtrar auditoría NPS:")
            b1, b2, b3 = st.columns(3)
            if b1.button(f"Promotores ({p_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Promotor"
            if b2.button(f"Pasivos ({pas_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Pasivo"
            if b3.button(f"Detractores ({d_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Detractor"

        with c2:
            st.plotly_chart(crear_gauge(csi_reloj, "CSI (Satisfacción)"), use_container_width=True)
            st.caption("Filtrar auditoría CSI:")
            bc1, bc2, bc3 = st.columns(3)
            if bc1.button(f"Excelente ({exc_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Excelente"
            if bc2.button(f"Regular ({reg_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Regular"
            if bc3.button(f"Malo ({mal_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Malo"

        # --- TABLA ---
        st.markdown("---")
        if st.session_state.f_tipo:
            # Lógica de filtrado para la tabla
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

    else: st.warning("No hay datos para este periodo.")
