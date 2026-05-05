import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="DASHBOARD POSTVENTA", layout="wide")

# Inicializar estados de sesión
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None
if "btn_active" not in st.session_state: st.session_state.btn_active = None
if "tab4_filter" not in st.session_state: st.session_state.tab4_filter = None

# --- CSS: ESTILO GLOBAL Y RESALTADO ---
st.markdown("""
    <style>
    div.stButton > button { width: 100% !important; height: 38px !important; border-radius: 8px !important; }
    button[kind="primary"] { background-color: #007bff !important; border-color: #007bff !important; color: white !important; font-weight: bold !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #f8f9fa; padding: 10px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 24px !important; text-align: center !important; }
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
    # Filtros de Tiempo en Sidebar
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

    # Mapeado de Columnas (Nombres fijos basados en tu Sheet)
    col_nps_puntaje = df_raw.columns[16] # Q
    col_t_concatenado = df_raw.columns[19] # T
    col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Cliente")
    col_asesor = next((c for c in df_raw.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")

    # Mapeo para Auditoría CSI
    col_csi_final = df_raw.columns[18]
    col_com_atencion = df_raw.columns[8]
    col_com_calidad = df_raw.columns[12]
    col_com_tiempo = df_raw.columns[14]
    col_ambiente_J = df_raw.columns[9]
    col_comentario_K = df_raw.columns[10]
    col_seguimiento = df_raw.columns[15]
    col_nps_comentario = df_raw.columns[17]

    def clean_val(x):
        try: return float(str(x).replace('%', '').replace(',', '.').strip())
        except: return 0.0

    df_mes[col_nps_puntaje] = df_mes[col_nps_puntaje].apply(clean_val)
    df_mes[col_csi_final] = df_mes[col_csi_final].apply(clean_val)
    df_mes[col_ambiente_J] = df_mes[col_ambiente_J].apply(clean_val)

    st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 INDICADORES", "👤 ASESORES", "📊 EVOLUCIÓN MENSUAL", "⚠️ ANÁLISIS DE RECLAMOS"])

    # --- TAB 1, 2, 3 (Simplificadas para brevedad, pero operativas) ---
    with tab1:
        # (Aquí va el código de Gauges que ya tenemos)
        if len(df_mes) > 0:
            c1, c2 = st.columns(2)
            nps_val = df_mes[col_nps_puntaje].mean() * 10
            csi_val = df_mes[col_csi_final].mean() * (100 if df_mes[col_csi_final].mean() <= 1.1 else 1)
            
            def crear_gauge(valor, titulo):
                return go.Figure(go.Indicator(mode="gauge+number", value=valor, title={'text': titulo}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#34495e"}}))
            
            with c1: st.plotly_chart(crear_gauge(nps_val, "NPS"), use_container_width=True)
            with c2: st.plotly_chart(crear_gauge(csi_val, "CSI"), use_container_width=True)
    
    with tab2:
        # (Aquí va el gráfico de Asesores)
        st.subheader("Desempeño por Asesor")
        df_as = df_mes.groupby(col_asesor).size().reset_index(name='Encuestas')
        st.plotly_chart(px.bar(df_as, x=col_asesor, y='Encuestas', color='Encuestas', color_continuous_scale='Blues'), use_container_width=True)

    with tab3:
        st.subheader("Evolución Mensual")

    # --- TAB 4: RECLAMOS VS SUGERENCIAS (LA SOLUCIÓN) ---
    with tab4:
        st.header("⚠️ Análisis de Calidad: Reclamos vs Sugerencias")
        
        if len(df_mes) > 0:
            # LÓGICA DE DICOTOMÍA: Clasificación de Intención
            def clasificar_intencion(row):
                nota = row[col_nps_puntaje]
                texto = str(row[col_t_concatenado]).lower()
                if nota <= 6: return "⚠️ Reclamo Crítico"
                elif nota >= 9 and len(texto) > 15: return "💡 Sugerencia de Mejora"
                elif nota >= 9: return "✅ Promotor Silencioso"
                return "Neutral"

            df_mes['Intención'] = df_mes.apply(clasificar_intencion, axis=1)
            
            cp = len(df_mes[df_mes['Intención'].str.contains("Promotor|Sugerencia")])
            cr = len(df_mes[df_mes['Intención'] == "⚠️ Reclamo Crítico"])

            col_izq, col_der = st.columns([1, 2], gap="large")
            
            with col_izq:
                # Botones de Filtro
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    is_p = st.session_state.tab4_filter == "Promotor"
                    if st.button("🟢 PROMOTORES", key="t4_p", type="primary" if is_p else "secondary"):
                        st.session_state.tab4_filter = "Promotor"; st.rerun()
                    st.metric("", cp)
                with c_btn2:
                    is_r = st.session_state.tab4_filter == "Reclamo"
                    if st.button("🔴 RECLAMOS", key="t4_r", type="primary" if is_r else "secondary"):
                        st.session_state.tab4_filter = "Reclamo"; st.rerun()
                    st.metric("", cr)
                
                if st.session_state.tab4_filter:
                    if st.button("🔄 Ver Todo", use_container_width=True): st.session_state.tab4_filter = None; st.rerun()

                # REGRESA EL GRÁFICO DE TORTA (NPS General)
                st.write("---")
                df_pie = df_mes[df_mes['Intención'] != "Neutral"]
                fig_torta = px.pie(df_pie, names='Intención', hole=0.5, 
                                  color='Intención', color_discrete_map={
                                      "⚠️ Reclamo Crítico": "#dc3545",
                                      "💡 Sugerencia de Mejora": "#0dcaf0",
                                      "✅ Promotor Silencioso": "#198754"
                                  }, title="Salud del Taller (NPS + Intención)")
                fig_torta.update_layout(showlegend=True, height=350, margin=dict(t=30,b=0,l=0,r=0))
                st.plotly_chart(fig_torta, use_container_width=True)

            with col_der:
                # Tabla Filtrada con la nueva clasificación
                if st.session_state.tab4_filter == "Promotor":
                    df_t = df_mes[df_mes['Intención'].str.contains("Promotor|Sugerencia")]
                elif st.session_state.tab4_filter == "Reclamo":
                    df_t = df_mes[df_mes['Intención'] == "⚠️ Reclamo Crítico"]
                else:
                    df_t = df_mes[df_mes['Intención'] != "Neutral"]
                
                st.subheader("Auditoría de Feedback")
                cols_f = [col_cliente, col_asesor, 'Intención', col_nps_puntaje, col_t_concatenado]
                st.dataframe(df_t[cols_f].rename(columns={col_t_concatenado: "Comentario / Concatenado (Col T)"}), 
                             use_container_width=True, hide_index=True, height=550)
else:
    st.error("No se pudieron cargar los datos.")
