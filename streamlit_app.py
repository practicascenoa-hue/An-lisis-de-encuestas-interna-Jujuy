import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="DASHBOARD POSTVENTA", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: ESTILO DE BOTONES Y PESTAÑAS ---
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }
    [data-testid="column"] [data-testid="column"] { padding: 0px 3px !important; }
    .stPlotlyChart { margin-bottom: -50px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=30)
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
    df_anio = df_raw[df_raw['Año'] == anio_sel].copy()
    
    meses_nros = sorted(df_anio['Mes_Num'].dropna().unique().astype(int))
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_nros])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    df_mes = df_anio[df_anio['Mes_Num'] == mes_sel_num].copy()

    # Mapeado de Columnas
    col_ambiente = df_raw.columns[9]     # Columna J
    col_nps_puntaje = df_raw.columns[16] # Columna Q
    col_csi_final = df_raw.columns[18]   # Columna S
    col_nps_comentario = df_raw.columns[17]
    col_comentario_I = df_raw.columns[8]
    col_comentario_M = df_raw.columns[12]
    col_comentario_O = df_raw.columns[14]
    col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Nombre y Apellido")
    col_asesor = next((c for c in df_raw.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")

    # Limpieza de datos
    def clean_val(x):
        try:
            val = float(str(x).replace('%', '').replace(',', '.').strip())
            return val
        except: return 0.0

    df_mes[col_nps_puntaje] = df_mes[col_nps_puntaje].apply(clean_val)
    df_mes[col_csi_final] = df_mes[col_csi_final].apply(clean_val)
    df_mes[col_ambiente] = df_mes[col_ambiente].apply(clean_val)

    st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")
    
    tab1, tab2 = st.tabs(["🎯 INDICADORES", "📊 VOLUMEN MENSUAL"])

    with tab1:
        if len(df_mes) > 0:
            # Cálculos
            nps_val = df_mes[col_nps_puntaje].mean() * 10
            csi_raw = df_mes[col_csi_final].mean()
            csi_val = csi_raw * 100 if csi_raw <= 1.1 else csi_raw
            amb_val = df_mes[col_ambiente].mean() * 10

            # --- FILA DE INDICADORES (RECUPERANDO SIMETRÍA) ---
            c1, c2 = st.columns(2)
            
            def crear_gauge(valor, titulo):
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=valor,
                    title={'text': f"<b>{titulo}</b>", 'font': {'size': 20}},
                    number={'valueformat': ".1f", 'suffix': "%", 'font': {'size': 50}},
                    gauge={'axis': {'range': [0, 100]},
                           'bar': {'color': "#34495e", 'thickness': 0.2},
                           'steps': [{'range': [0, 60], 'color': "#f8d7da"},
                                     {'range': [60, 90], 'color': "#fff3cd"},
                                     {'range': [90, 100], 'color': "#d1e7dd"}]}
                ))
                fig.update_layout(height=280, margin=dict(l=50, r=50, t=80, b=0), paper_bgcolor='rgba(0,0,0,0)')
                return fig

            with c1:
                st.plotly_chart(crear_gauge(nps_val, "NPS (Recomendación)"), use_container_width=True)
                # Botones NPS bajo su indicador
                v1, b1, b2, b3, v2 = st.columns([0.2, 1, 1, 1, 0.2])
                p_c = len(df_mes[df_mes[col_nps_puntaje] >= 9])
                d_c = len(df_mes[df_mes[col_nps_puntaje] <= 6])
                pas_c = len(df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)])
                with b1: st.button(f"🟢 {p_c} Prom", key="p1", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Promotor"}))
                with b2: st.button(f"🟡 {pas_c} Neu", key="p2", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo"}))
                with b3: st.button(f"🔴 {d_c} Det", key="p3", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Detractor"}))

            with c2:
                st.plotly_chart(crear_gauge(csi_val, "CSI (Satisfacción)"), use_container_width=True)
                # Botones CSI bajo su indicador
                v3, bc1, bc2, bc3, v4 = st.columns([0.2, 1, 1, 1, 0.2])
                limit = 90 if csi_val > 15 else 9
                exc_c = len(df_mes[df_mes[col_csi_final] >= limit])
                mal_c = len(df_mes[df_mes[col_csi_final] <= (limit-30 if limit==90 else 6)])
                reg_c = len(df_mes) - exc_c - mal_c
                with bc1: st.button(f"🟢 {exc_c} Exc", key="e1", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Excelente"}))
                with bc2: st.button(f"🟡 {reg_c} Reg", key="e2", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Regular"}))
                with bc3: st.button(f"🔴 {mal_c} Mal", key="e3", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Malo"}))

            # --- TARJETA DE AMBIENTE ABAJO Y ALARGADA ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 12px; border: 1px solid #dee2e6; text-align: center; width: 100%;">
                    <span style="color: #495057; font-size: 16px; font-weight: bold;">🏢 SATISFACCIÓN AMBIENTE TALLER (Col J): </span>
                    <span style="color: #2c3e50; font-size: 24px; font-weight: bold; margin-left: 10px;">{amb_val:.1f}%</span>
                </div>
            """, unsafe_allow_html=True)

            if st.session_state.f_tipo:
                st.markdown("---")
                st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
                if st.session_state.f_tipo == "NPS":
                    if st.session_state.f_val == "Promotor": df_f = df_mes[df_mes[col_nps_puntaje] >= 9]
                    elif st.session_state.f_val == "Detractor": df_f = df_mes[df_mes[col_nps_puntaje] <= 6]
                    else: df_f = df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)]
                    cols_v = [col_cliente, col_asesor, col_ambiente, col_nps_puntaje, col_nps_comentario]
                else:
                    if st.session_state.f_val == "Excelente": df_f = df_mes[df_mes[col_csi_final] >= limit]
                    elif st.session_state.f_val == "Malo": df_f = df_mes[df_mes[col_csi_final] <= (limit-30 if limit==90 else 6)]
                    else: df_f = df_mes[(df_mes[col_csi_final] < limit) & (df_mes[col_csi_final] > (limit-30 if limit==90 else 6))]
                    cols_v = [col_cliente, col_asesor, col_ambiente, col_csi_final, col_comentario_I, col_comentario_M, col_comentario_O]
                st.dataframe(df_f[cols_v].fillna("Sin comentario"), use_container_width=True)

    with tab2:
        st.subheader(f"Evolución Mensual - {anio_sel}")
        df_anio[col_csi_final] = df_anio[col_csi_final].apply(clean_val)
        df_anio[col_nps_puntaje] = df_anio[col_nps_puntaje].apply(clean_val)
        df_counts = df_anio.groupby('Mes_Num').size().reset_index(name='Encuestas')
        df_means = df_anio.groupby('Mes_Num')[[col_csi_final, col_nps_puntaje]].mean().reset_index()
        df_vol = pd.merge(df_counts, df_means, on='Mes_Num')
        df_vol['Mes'] = df_vol['Mes_Num'].map(meses_dict)
        df_vol['NPS_Scale'] = df_vol[col_nps_puntaje] * 10
        fig_bar = px.bar(df_vol, y='Mes', x='Encuestas', orientation='h', text='Encuestas', color='Encuestas', color_continuous_scale='Sunset',
                         labels={'Encuestas': 'Volumen', 'Mes': 'Mes', col_csi_final: 'CSI (%)', 'NPS_Scale': 'NPS (%)'},
                         hover_data={'Mes': False, 'Encuestas': True, col_csi_final: ':.1f', 'NPS_Scale': ':.1f'})
        fig_bar.update_layout(yaxis={'categoryorder':'array', 'categoryarray':list(meses_dict.values())[::-1]}, height=500, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.error("No se pudieron cargar los datos.")
