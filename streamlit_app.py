import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="ENCUESTAS DE SATISFACCIÓN TALLER Cenoa", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: ESTILO DE BOTONES Y PESTAÑAS (FORZADO) ---
st.markdown("""
    <style>
    /* Estilo de los botones tipo Badge */
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
    
    /* Estilo visual para que las pestañas resalten */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f3f5;
        padding: 10px 10px 0px 10px;
        border-radius: 10px 10px 0px 0px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f3f5;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        border-bottom: 2px solid #007bff !important;
    }

    [data-testid="column"] [data-testid="column"] { padding: 0px 3px !important; }
    .stPlotlyChart { margin-bottom: -45px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=30) # Bajamos el TTL para que refresque más rápido
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
    # Sidebar: Filtros
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

    # Mapeado de Columnas (Q, R, I, M, O, S)
    col_nps_puntaje = df_raw.columns[16]    # Q
    col_nps_comentario = df_raw.columns[17] # R
    col_comentario_I = df_raw.columns[8]    # I
    col_comentario_M = df_raw.columns[12]   # M
    col_comentario_O = df_raw.columns[14]   # O
    col_csi_final = df_raw.columns[18]      # S
    col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Nombre y Apellido")
    col_asesor = next((c for c in df_raw.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")

    # --- PESTAÑAS PRINCIPALES ---
    tab1, tab2 = st.tabs(["🎯 INDICADORES DE SATISFACCIÓN", "📊 VOLUMEN MENSUAL"])

    with tab1:
        st.title("INDICADORES DE SATISFACCIÓN")
        if len(df_mes) > 0:
            df_mes[col_nps_puntaje] = pd.to_numeric(df_mes[col_nps_puntaje], errors='coerce')
            df_mes[col_csi_final] = df_mes[col_csi_final].astype(str).str.replace('%', '').str.replace(',', '.')
            df_mes[col_csi_final] = pd.to_numeric(df_mes[col_csi_final], errors='coerce')

            nps_val = df_mes[col_nps_puntaje].mean() * 10 if not df_mes.dropna(subset=[col_nps_puntaje]).empty else 0
            df_csi_v = df_mes.dropna(subset=[col_csi_final])
            csi_val = (df_csi_v[col_csi_final].mean() * 100 if not df_csi_v.empty and df_csi_v[col_csi_final].max() <= 1.1 else df_csi_v[col_csi_final].mean()) if not df_csi_v.empty else 0
            
            p_c = len(df_mes[df_mes[col_nps_puntaje] >= 9]); d_c = len(df_mes[df_mes[col_nps_puntaje] <= 6]); pas_c = len(df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)])
            l_e = 9 if csi_val < 15 else 90; l_m = 6 if csi_val < 15 else 60
            exc_c = len(df_mes[df_mes[col_csi_final] >= l_e]); mal_c = len(df_mes[df_mes[col_csi_final] <= l_m]); reg_c = len(df_mes) - exc_c - mal_c

            def crear_gauge(valor, titulo):
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=valor,
                    title={'text': f"<b>{titulo}</b>", 'font': {'size': 18}},
                    number={'valueformat': ".1f" if "CSI" in titulo else ".0f", 'font': {'size': 45}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#34495e", 'thickness': 0.2},
                           'steps': [{'range': [0, 60], 'color': "#f8d7da"}, {'range': [60, 90], 'color': "#fff3cd"}, {'range': [90, 100], 'color': "#d1e7dd"}]}
                ))
                fig.update_layout(height=230, margin=dict(l=50, r=50, t=70, b=0), paper_bgcolor='rgba(0,0,0,0)')
                return fig

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

            if st.session_state.f_tipo:
                st.markdown("---")
                st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
                if st.session_state.f_tipo == "NPS":
                    if st.session_state.f_val == "Promotor": df_f = df_mes[df_mes[col_nps_puntaje] >= 9]
                    elif st.session_state.f_val == "Detractor": df_f = df_mes[df_mes[col_nps_puntaje] <= 6]
                    else: df_f = df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)]
                    cols_v = [col_cliente, col_asesor, col_nps_puntaje, col_nps_comentario]
                else:
                    if st.session_state.f_val == "Excelente": df_f = df_mes[df_mes[col_csi_final] >= l_e]
                    elif st.session_state.f_val == "Malo": df_f = df_mes[df_mes[col_csi_final] <= l_m]
                    else: df_f = df_mes[(df_mes[col_csi_final] > l_m) & (df_mes[col_csi_final] < l_e)]
                    cols_v = [col_cliente, col_asesor, col_csi_final, col_comentario_I, col_comentario_M, col_comentario_O]
                st.dataframe(df_f[cols_v].fillna("Sin comentario"), use_container_width=True)
        else: st.warning("Sin datos para este periodo.")

    with tab2:
        st.title("ESTADÍSTICAS DE VOLUMEN")
        st.subheader(f"Total de Encuestas por Mes en {anio_sel}")
        df_vol = df_anio.groupby('Mes_Num').size().reset_index(name='Encuestas')
        df_vol['Mes'] = df_vol['Mes_Num'].map(meses_dict)
        
        fig_bar = px.bar(
            df_vol, x='Mes', y='Encuestas', text='Encuestas',
            labels={'Encuestas': 'Total Encuestas', 'Mes': 'Mes'},
            color='Encuestas', color_continuous_scale='Blues'
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(xaxis={'categoryorder':'array', 'categoryarray':list(meses_dict.values())})
        st.plotly_chart(fig_bar, use_container_width=True)

else: st.error("No se pudieron cargar los datos.")
