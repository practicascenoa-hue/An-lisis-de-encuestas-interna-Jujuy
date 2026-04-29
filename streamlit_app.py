import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración y Estilo CSS para botones modernos
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

st.markdown("""
    <style>
    /* Estilo para los botones de Promotores, Pasivos y Detractores */
    div.stButton > button {
        width: 100%;
        height: 80px;
        border-radius: 15px;
        border: none;
        color: white;
        font-weight: bold;
        font-size: 18px;
        transition: 0.3s;
    }
    /* Color Verde para Promotores */
    div.stButton > button:first-child { background-color: #28a745; }
    /* Color Amarillo para Pasivos */
    div.stButton > button:nth-child(2) { background-color: #ffc107; color: black; }
    /* Color Rojo para Detractores */
    div.stButton > button:last-child { background-color: #dc3545; }
    
    div.stButton > button:hover {
        opacity: 0.8;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_stdio=True)

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
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    # Filtros de Tiempo
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year.astype(int)
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month.astype(int)
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                  7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("⚙️ Filtros")
    anio_sel = st.sidebar.selectbox("Año", sorted(df_raw['Año'].unique(), reverse=True))
    meses_disp = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].unique())
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_disp])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # Identificación de columnas
    col_nps_preg = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    col_calidad = next((c for c in df.columns if "chapa" in c.lower() or "calidad" in c.lower()), None)
    col_tiempo = next((c for c in df.columns if "acordada" in c.lower() or "tiempo" in c.lower()), None)
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), None)
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), None)
    col_coment = next((c for c in df.columns if "porque" in c.lower() or "comentario" in c.lower()), None)

    st.title("🚀 Dashboard de Calidad Cenoa")

    if col_nps_preg and len(df) > 0:
        df[col_nps_preg] = pd.to_numeric(df[col_nps_preg], errors='coerce')
        df = df.dropna(subset=[col_nps_preg])
        
        total = len(df)
        df['Segmento'] = df[col_nps_preg].apply(lambda x: 'Promotor' if x >= 9 else ('Detractor' if x <= 6 else 'Pasivo'))
        
        prom = df[df['Segmento'] == 'Promotor']
        pas = df[df['Segmento'] == 'Pasivo']
        det = df[df['Segmento'] == 'Detractor']
        
        nps_score = ((len(prom) - len(det)) / total) * 100

        # CSI
        df['v_calidad'] = pd.to_numeric(df[col_calidad], errors='coerce') if col_calidad else 0
        def conv_t(v):
            v_s = str(v).lower()
            return 10 if "si" in v_s or "sí" in v_s else (0 if "no" in v_s else pd.to_numeric(v, errors='coerce'))
        df['v_tiempo'] = df[col_tiempo].apply(conv_t) if col_tiempo else 0
        csi_score = df[['v_calidad', 'v_tiempo']].mean(axis=1).mean()

        # --- RELOJES ---
        c1, c2 = st.columns(2)
        with c1:
            fig_nps = go.Figure(go.Indicator(
                mode = "gauge+number", value = nps_score, title = {'text': "NPS Recomendación"},
                gauge = {'axis': {'range': [-100, 100]}, 'bar': {'color': "black"},
                         'steps': [{'range': [-100, 0], 'color': "#FF4B4B"},
                                   {'range': 0, 70], 'color': "#FFA500"},
                                   {'range': 70, 100], 'color': "#00CC96"}]}))
            st.plotly_chart(fig_nps, use_container_width=True)
            
            # --- BOTONES ESTILIZADOS ---
            st.markdown("### Seleccione un grupo para auditar:")
            if "btn_state" not in st.session_state: st.session_state.btn_state = None

            b1, b2, b3 = st.columns(3)
            # Cada botón actúa como una tarjeta de KPI
            if b1.button(f"PROMOTORES\n{len(prom)}"): st.session_state.btn_state = "Promotor"
            if b2.button(f"PASIVOS\n{len(pas)}"): st.session_state.btn_state = "Pasivo"
            if b3.button(f"DETRACTORES\n{len(det)}"): st.session_state.btn_state = "Detractor"

        with c2:
            fig_csi = go.Figure(go.Indicator(
                mode = "gauge+number", value = csi_score, title = {'text': "CSI (Calidad + Tiempo)"},
                gauge = {'axis': {'range': [0, 10]}, 'bar': {'color': "black"},
                         'steps': [{'range': [0, 7], 'color': "#FF4B4B"},
                                   {'range': 7, 8.5], 'color': "#FFA500"},
                                   {'range': 8.5, 10], 'color': "#00CC96"}]}))
            st.plotly_chart(fig_csi, use_container_width=True)

        # --- MOSTRAR LISTADO ---
        st.markdown("---")
        cols_finales = [c for c in [col_cliente, col_asesor, col_nps_preg, col_coment] if c is not None]

        if st.session_state.btn_state:
            df_filtro = df[df['Segmento'] == st.session_state.btn_state]
            color_msg = "success" if st.session_state.btn_state == "Promotor" else ("warning" if st.session_state.btn_state == "Pasivo" else "error")
            
            getattr(st, color_msg)(f"Mostrando detalle de {st.session_state.btn_state}s")
            st.dataframe(df_filtro[cols_finales], use_container_width=True)
        else:
            st.info("Haga clic en una de las tarjetas de colores arriba para ver el listado de clientes.")

    else: st.warning("Sin datos.")
