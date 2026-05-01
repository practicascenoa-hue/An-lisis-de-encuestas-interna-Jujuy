import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="ENCUESTAS DE SATISFACCIÓN TALLER Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: ESTILO DE BOTONES Y ALINEACIÓN ---
st.markdown("""
    <style>
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
    [data-testid="column"] [data-testid="column"] {
        padding: 0px 3px !important;
    }
    div.stButton { margin-top: 10px; }
    .stPlotlyChart { margin-bottom: -45px; }
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
    # Sidebar: Filtros de Periodo
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("FILTROS PERIODO")
    anio_sel = st.sidebar.selectbox("Año", sorted(df_raw['Año'].dropna().unique().astype(int), reverse=True))
    meses_nros = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].dropna().unique().astype(int))
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_nros])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # --- MAPEADO DE COLUMNAS SEGÚN SHEET ---
    # NPS: Recomendación
    col_nps_puntaje = df.columns[16]    # Columna Q (Índice 16)
    col_nps_comentario = df.columns[17] # Columna R (Índice 17)
    
    # CSI: Satisfacción y Comentarios
    col_comentario_I = df.columns[8]   # Comentario Atención (I)
    col_comentario_M = df.columns[12]  # Comentario Calidad (M)
    col_comentario_O = df.columns[14]  # Comentario Tiempo (O)
    col_csi_final = df.columns[18]     # Columna S (Índice 18)
    
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Nombre y Apellido")
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")

    st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")

    if len(df) > 0:
        # Procesamiento numérico
        df[col_nps_puntaje] = pd.to_numeric(df[col_nps_puntaje], errors='coerce')
        df[col_csi_final] = df[col_csi_final].astype(str).str.replace('%', '').str.replace(',', '.')
        df[col_csi_final] = pd.to_numeric(df[col_csi_final], errors='coerce')

        nps_val = df[col_nps_puntaje].mean() * 10 if not df.dropna(subset=[col_nps_puntaje]).empty else 0
        
        df_csi_v = df.dropna(subset=[col_csi_final])
        csi_val = (df_csi_v[col_csi_final].mean() * 100 if not df_csi_v.empty and df_csi_v[col_csi_final].max() <= 1.1 else df_csi_v[col_csi_final].mean()) if not df_csi_v.empty else 0
        
        # Conteos para los botones
        p_c = len(df[df[col_nps_puntaje] >= 9]); d_c = len(df[df[col_nps_puntaje] <= 6]); pas_c = len(df[(df[col_nps_puntaje] > 6) & (df[col_nps_puntaje] < 9)])
        l_e = 9 if csi_val < 15 else 90; l_m = 6 if csi_val < 15 else 60
        exc_c = len(df[df[col_csi_final] >= l_e]); mal_c = len(df[df[col_csi_final] <= l_m]); reg_c = len(df) - exc_c - mal_c

        def crear_gauge(valor, titulo):
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=valor,
                title={'text': f"<b>{titulo}</b>", 'font': {'size': 20, 'color': '#2c3e50'}},
                number={'valueformat': ".1f" if "CSI" in titulo else ".0f", 'font': {'size': 50}},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#34495e", 'thickness': 0.2},
                       'steps': [{'range': [0, 60], 'color': "#f8d7da"}, {'range': [60, 90], 'color': "#fff3cd"}, {'range': [90, 100], 'color': "#d1e7dd"}]}
            ))
            fig.update_layout(height=260, margin=dict(l=60, r=60, t=80, b=0), paper_bgcolor='rgba(0,0,0,0)')
            return fig

        # --- GRID DE INDICADORES ---
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(crear_gauge(nps_val, "NPS (Recomendación)"), use_container_width=True)
            v1, bn1, bn2, bn3, v2 = st.columns([0.7, 1, 1, 1, 0.3])
            with bn1: st.button(f"🟢 {p_c} Prom", key="p1", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Promotor"}))
            with bn2: st.button(f"🟡 {pas_c} Neu", key="p2", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo"}))
            with bn3: st.button(f"🔴 {d_c} Det", key="p3", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Detractor"}))

        with c2:
            st.plotly_chart(crear_gauge(csi_val, "CSI (Satisfacción)"), use_container_width=True)
            v3, bc1, bc2, bc3, v4 = st.columns([0.7, 1, 1, 1, 0.3])
            with bc1: st.button(f"🟢 {exc_c} Exc", key="e1", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Excelente"}))
            with bc2: st.button(f"🟡 {reg_c} Reg", key="e2", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Regular"}))
            with bc3: st.button(f"🔴 {mal_c} Mal", key="e3", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Malo"}))

        # --- TABLA DINÁMICA DE AUDITORÍA ---
        if st.session_state.f_tipo:
            st.markdown("---")
            st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
            
            if st.session_state.f_tipo == "NPS":
                # Filtrado NPS basado en Columna Q
                if st.session_state.f_val == "Promotor": df_f = df[df[col_nps_puntaje] >= 9]
                elif st.session_state.f_val == "Detractor": df_f = df[df[col_nps_puntaje] <= 6]
                else: df_f = df[(df[col_nps_puntaje] > 6) & (df[col_nps_puntaje] < 9)]
                
                # Columnas NPS: Nombre, Asesor, Puntaje (Q) y Comentario (R)
                cols_v = [col_cliente, col_asesor, col_nps_puntaje, col_nps_comentario]
            else:
                # Filtrado CSI basado en Columna S
                if st.session_state.f_val == "Excelente": df_f = df[df[col_csi_final] >= l_e]
                elif st.session_state.f_val == "Malo": df_f = df[df[col_csi_final] <= l_m]
                else: df_f = df[(df[col_csi_final] > l_m) & (df[col_csi_final] < l_e)]
                
                # Columnas CSI: Nombre, Asesor, CSI Final (S) y Comentarios de I, M, O
                cols_v = [col_cliente, col_asesor, col_csi_final, col_comentario_I, col_comentario_M, col_comentario_O]

            st.dataframe(df_f[cols_v].fillna("Sin comentario"), use_container_width=True)

    else: st.warning("Sin datos para este periodo.")
