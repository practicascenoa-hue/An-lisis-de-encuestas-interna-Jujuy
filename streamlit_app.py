import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="DASHBOARD POSTVENTA", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None
if "btn_active" not in st.session_state: st.session_state.btn_active = None
if "tab4_filter" not in st.session_state: st.session_state.tab4_filter = None # Inicia en None para ver todo

# --- CSS: ESTILO DEFINITIVO ---
st.markdown("""
    <style>
    div.stButton > button {
        width: 100% !important;
        height: 38px !important;
        border-radius: 8px !important;
    }
    /* Estilo para botón seleccionado (Azul profesional) */
    button[kind="primary"] {
        background-color: #007bff !important;
        border-color: #007bff !important;
        color: white !important;
        font-weight: bold !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] { font-weight: bold; }
    .stPlotlyChart { margin-bottom: -10px !important; }
    [data-testid="stMetricValue"] { font-size: 24px !important; text-align: center !important; }
    [data-testid="stMetricLabel"] { text-align: center !important; width: 100%; }
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
    col_nps_puntaje = df_raw.columns[16] # Q
    col_t_concatenado = df_raw.columns[19] # T
    col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Cliente")
    col_asesor = next((c for c in df_raw.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")

    def clean_val(x):
        try: return float(str(x).replace('%', '').replace(',', '.').strip())
        except: return 0.0

    df_mes[col_nps_puntaje] = df_mes[col_nps_puntaje].apply(clean_val)

    # 4 Pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 INDICADORES", "👤 ASESORES", "📊 EVOLUCIÓN MENSUAL", "⚠️ ANÁLISIS DE RECLAMOS"])

    # ... (Tab 1, 2 y 3 se mantienen igual que en versiones anteriores)

    with tab4:
        st.header("⚠️ Análisis de Reclamos vs. Promotores (NPS)")
        
        if len(df_mes) > 0:
            # Categorización NPS
            df_mes['Segmento_NPS'] = df_mes[col_nps_puntaje].apply(
                lambda x: 'Promotor' if x >= 9 else ('Reclamo' if x <= 6 else 'Pasivo')
            )
            
            cant_promotores = len(df_mes[df_mes['Segmento_NPS'] == 'Promotor'])
            cant_reclamos = len(df_mes[df_mes['Segmento_NPS'] == 'Reclamo'])

            # LAYOUT DE DOS COLUMNAS
            col_izq, col_der = st.columns([1, 2], gap="large")

            with col_izq:
                # Botones de Filtro
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    is_p = st.session_state.tab4_filter == "Promotor"
                    if st.button("🟢 PROMOTORES", key="t4_p", type="primary" if is_p else "secondary"):
                        st.session_state.tab4_filter = "Promotor"
                        st.rerun()
                    st.metric("", cant_promotores)
                
                with c_btn2:
                    is_r = st.session_state.tab4_filter == "Reclamo"
                    if st.button("🔴 RECLAMOS", key="t4_r", type="primary" if is_r else "secondary"):
                        st.session_state.tab4_filter = "Reclamo"
                        st.rerun()
                    st.metric("", cant_reclamos)
                
                if st.session_state.tab4_filter is not None:
                    if st.button("🔄 Ver Todo", use_container_width=True):
                        st.session_state.tab4_filter = None
                        st.rerun()

                st.write("") # Espaciador

                # Gráfico de Torta
                df_pie = df_mes[df_mes['Segmento_NPS'].isin(['Promotor', 'Reclamo'])]
                if not df_pie.empty:
                    resumen_pie = df_pie['Segmento_NPS'].value_counts().reset_index()
                    resumen_pie.columns = ['Tipo', 'Cantidad']
                    fig_torta = px.pie(resumen_pie, values='Cantidad', names='Tipo', hole=0.5,
                                      color='Tipo', color_discrete_map={'Promotor': '#198754', 'Reclamo': '#dc3545'})
                    fig_torta.update_layout(showlegend=True, height=350, margin=dict(t=0, b=0, l=0, r=0))
                    fig_torta.update_traces(textinfo='percent')
                    st.plotly_chart(fig_torta, use_container_width=True)

            with col_der:
                # Lógica de Filtrado de Tabla
                if st.session_state.tab4_filter:
                    st.subheader(f"Listado: {st.session_state.tab4_filter}es")
                    df_tabla = df_mes[df_mes['Segmento_NPS'] == st.session_state.tab4_filter]
                else:
                    st.subheader("Listado General (Promotores y Reclamos)")
                    df_tabla = df_mes[df_mes['Segmento_NPS'].isin(['Promotor', 'Reclamo'])]
                
                cols_mostrar = [col_cliente, col_asesor, col_nps_puntaje, col_t_concatenado]
                st.dataframe(
                    df_tabla[cols_mostrar].rename(columns={col_t_concatenado: "Comentario / Concatenado (Col T)"}), 
                    use_container_width=True, 
                    hide_index=True,
                    height=550 # Altura fija para que coincida con el gráfico
                )
        else:
            st.warning("No hay datos suficientes para el periodo seleccionado.")
else:
    st.error("No se pudieron cargar los datos.")
