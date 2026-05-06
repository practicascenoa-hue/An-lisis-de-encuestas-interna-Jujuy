import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="DASHBOARD POSTVENTA V2",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialización de estados de sesión (Session State)
if "f_tipo" not in st.session_state:
    st.session_state.f_tipo = None
if "f_val" not in st.session_state:
    st.session_state.f_val = None
if "btn_active" not in st.session_state:
    st.session_state.btn_active = None
if "tab4_filter" not in st.session_state:
    st.session_state.tab4_filter = None

# ==========================================
# 2. ESTILOS CSS PERSONALIZADOS
# ==========================================
st.markdown("""
    <style>
    /* Botones principales */
    div.stButton > button {
        width: 100% !important;
        height: 42px !important;
        border-radius: 10px !important;
        transition: all 0.3s ease;
    }
    
    /* Resaltado de botones activos */
    button[kind="primary"] {
        background-color: #007bff !important;
        border-color: #007bff !important;
        color: white !important;
        font-weight: bold !important;
        box-shadow: 0px 4px 10px rgba(0, 123, 255, 0.3);
    }

    /* Estilo de las pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: #f1f3f5;
        padding: 12px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 700;
        color: #495057;
    }

    /* FORZAR TEXTO COMPLETO EN TABLAS (WRAP) */
    [data-testid="stTable"] td, 
    [data-testid="stDataFrame"] td, 
    .stDataFrame div[data-testid="stTable"] div {
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.4 !important;
        vertical-align: middle !important;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        text-align: center !important;
        font-weight: 800 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CARGA Y PROCESAMIENTO DE DATOS
# ==========================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        col_fecha = "Marca temporal"
        if col_fecha in df.columns:
            df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
        return df.dropna(how='all'), col_fecha
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    # --- MAPEADO DE COLUMNAS ORIGINALES ---
    col_comentario_K = df_raw.columns[10] 
    col_ambiente_J = df_raw.columns[9]    
    col_seguimiento = df_raw.columns[15]  
    col_nps_puntaje = df_raw.columns[16]  
    col_csi_final = df_raw.columns[18]    
    col_nps_comentario = df_raw.columns[17] 
    col_com_atencion = df_raw.columns[8]  
    col_com_calidad = df_raw.columns[12]  
    col_com_tiempo = df_raw.columns[14]   
    col_t_concatenado = df_raw.columns[19] 
    
    # Identificar Cliente y Asesor dinámicamente
    col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Cliente")
    col_asesor = next((c for c in df_raw.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")

    # Función de limpieza numérica
    def clean_val(x):
        try:
            return float(str(x).replace('%', '').replace(',', '.').strip())
        except:
            return 0.0

    # Limpieza de indicadores principales
    df_raw[col_nps_puntaje] = df_raw[col_nps_puntaje].apply(clean_val)
    df_raw[col_csi_final] = df_raw[col_csi_final].apply(clean_val)
    df_raw[col_ambiente_J] = df_raw[col_ambiente_J].apply(clean_val)

    # Sidebar: Filtros Temporales
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month
    
    meses_nombres = {
        1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
        7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
    }
    
    st.sidebar.header("🗓️ PERIODO DE ANÁLISIS")
    anios_disp = sorted(df_raw['Año'].dropna().unique().astype(int), reverse=True)
    anio_sel = st.sidebar.selectbox("Seleccione Año", anios_disp)
    
    df_anio = df_raw[df_raw['Año'] == anio_sel].copy()
    meses_disp_nros = sorted(df_anio['Mes_Num'].dropna().unique().astype(int))
    mes_sel_nombre = st.sidebar.selectbox("Seleccione Mes", [meses_nombres[m] for m in meses_disp_nros])
    
    mes_sel_num = [k for k, v in meses_nombres.items() if v == mes_sel_nombre][0]
    df_mes = df_anio[df_anio['Mes_Num'] == mes_sel_num].copy()

    st.title("📊 INDICADORES ENCUESTAS DE SATISFACCIÓN")
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 KPIs PRINCIPALES", "👤 GESTIÓN ASESORES", "📈 EVOLUCIÓN", "⚠️ AUDITORÍA RECLAMOS"])

    # ==========================================
    # TAB 1: INDICADORES (KPIs)
    # ==========================================
    with tab1:
        if len(df_mes) > 0:
            # Cálculo de valores
            nps_avg = df_mes[col_nps_puntaje].mean() * 10
            csi_raw_avg = df_mes[col_csi_final].mean()
            csi_final_avg = csi_raw_avg * 100 if csi_raw_avg <= 1.1 else csi_raw_avg
            amb_avg = df_mes[col_ambiente_J].mean() * 10

            col_g1, col_g2 = st.columns(2)
            
            def render_gauge(valor, titulo, color_bar="#34495e"):
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=valor,
                    title={'text': f"<b>{titulo}</b>", 'font': {'size': 20}},
                    number={'suffix': "%", 'valueformat': ".1f"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': color_bar},
                        'steps': [
                            {'range': [0, 60], 'color': "#f8d7da"},
                            {'range': [60, 90], 'color': "#fff3cd"},
                            {'range': [90, 100], 'color': "#d1e7dd"}
                        ]
                    }
                ))
                fig.update_layout(height=300, margin=dict(l=30, r=30, t=50, b=20))
                return fig

            with col_g1:
                st.plotly_chart(render_gauge(nps_avg, "NPS (Net Promoter Score)"), use_container_width=True)
                # Botones de filtrado NPS
                p_count = len(df_mes[df_mes[col_nps_puntaje] >= 9])
                d_count = len(df_mes[df_mes[col_nps_puntaje] <= 6])
                neu_count = len(df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)])
                
                c_b1, c_b2, c_b3 = st.columns(3)
                if c_b1.button(f"🟢 {p_count} Promotores", key="nps_p"):
                    st.session_state.update({"f_tipo":"NPS","f_val":"Promotor", "btn_active":"btn1"}); st.rerun()
                if c_b2.button(f"🟡 {neu_count} Neutrales", key="nps_n"):
                    st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo", "btn_active":"btn2"}); st.rerun()
                if c_b3.button(f"🔴 {d_count} Detractores", key="nps_d"):
                    st.session_state.update({"f_tipo":"NPS","f_val":"Detractor", "btn_active":"btn3"}); st.rerun()

            with col_g2:
                st.plotly_chart(render_gauge(csi_final_avg, "CSI (Customer Satisfaction)"), use_container_width=True)
                # Lógica de estados CSI
                csi_limit = 90 if csi_final_avg > 15 else 9
                exc_count = len(df_mes[df_mes[col_csi_final] >= csi_limit])
                mal_count = len(df_mes[df_mes[col_csi_final] <= 6])
                reg_count = len(df_mes) - exc_count - mal_count

                c_b4, c_b5, c_b6 = st.columns(3)
                if c_b4.button(f"🟢 {exc_count} Excelente", key="csi_e"):
                    st.session_state.update({"f_tipo":"CSI","f_val":"Excelente", "btn_active":"btn4"}); st.rerun()
                if c_b5.button(f"🟡 {reg_count} Regular", key="csi_r"):
                    st.session_state.update({"f_tipo":"CSI","f_val":"Regular", "btn_active":"btn5"}); st.rerun()
                if c_b6.button(f"🔴 {mal_count} Malo", key="csi_m"):
                    st.session_state.update({"f_tipo":"CSI","f_val":"Malo", "btn_active":"btn6"}); st.rerun()

            st.markdown(f"""<div style="background-color:#f8f9fa; border:1px solid #dee2e6; padding:15px; border-radius:10px; text-align:center; margin-top:20px;">
                <h4 style="margin:0; color:#495057;">🏢 SATISFACCIÓN AMBIENTE TALLER: <b>{amb_avg:.1f}%</b></h4>
            </div>""", unsafe_allow_html=True)

            # Tabla de auditoría interna de la pestaña 1
            if st.session_state.f_tipo:
                st.write("---")
                st.subheader(f"Detalle de Selección: {st.session_state.f_val}")
                if st.session_state.f_tipo == "NPS":
                    df_det = df_mes[df_mes[col_nps_puntaje] >= 9] if st.session_state.f_val == "Promotor" else (df_mes[df_mes[col_nps_puntaje] <= 6] if st.session_state.f_val == "Detractor" else df_mes[(df_mes[col_nps_puntaje]>6)&(df_mes[col_nps_puntaje]<9)])
                    cols_show = [col_cliente, col_asesor, col_nps_puntaje, col_nps_comentario]
                else:
                    df_det = df_mes[df_mes[col_csi_final] >= csi_limit] if st.session_state.f_val == "Excelente" else (df_mes[df_mes[col_csi_final] <= 6] if st.session_state.f_val == "Malo" else df_mes[(df_mes[col_csi_final]<csi_limit)&(df_mes[col_csi_final]>6)])
                    cols_show = [col_cliente, col_asesor, col_csi_final, col_com_atencion, col_com_calidad, col_com_tiempo]
                st.dataframe(df_det[cols_show].fillna("No registra"), use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 2: GESTIÓN DE ASESORES
    # ==========================================
    with tab2:
        st.subheader(f"Productividad y Seguimiento - {mes_sel_nombre}")
        if len(df_mes) > 0:
            df_asesores = df_mes.groupby(col_asesor).size().reset_index(name='Total Encuestas')
            fig_bar_as = px.bar(df_asesores, x=col_asesor, y='Total Encuestas', text='Total Encuestas', color='Total Encuestas', color_continuous_scale='Blues')
            fig_bar_as.update_layout(xaxis_title="Asesor", yaxis_title="Cantidad", showlegend=False)
            st.plotly_chart(fig_bar_as, use_container_width=True)
            
            st.write("---")
            col_p1, col_p2 = st.columns([1, 2])
            with col_p1:
                st.markdown("**¿Se realizó seguimiento telefónico?**")
                pie_data = df_mes[col_seguimiento].fillna("Sin Datos").value_counts().reset_index()
                st.plotly_chart(px.pie(pie_data, names=pie_data.columns[0], values='count', hole=0.4), use_container_width=True)
            with col_p2:
                df_mes['Seg_Num'] = df_mes[col_seguimiento].apply(lambda x: 1 if str(x).lower().strip() == 'sí' else 0)
                res_seg = df_mes.groupby(col_asesor).agg(Total=('Seg_Num', 'count'), Si=('Seg_Num', 'sum')).reset_index()
                res_seg['% Eficacia'] = (res_seg['Si'] / res_seg['Total'] * 100).round(1).astype(str) + "%"
                st.dataframe(res_seg.rename(columns={'Total': 'Encuestas Totales', 'Si': 'Con Seguimiento'}), use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 3: EVOLUCIÓN MENSUAL
    # ==========================================
    with tab3:
        st.subheader(f"Tendencia de Satisfacción {anio_sel}")
        df_evo = df_anio.groupby('Mes_Num').agg({col_fecha_nombre: 'count', col_csi_final: 'mean', col_nps_puntaje: 'mean'}).reset_index()
        df_evo['Mes'] = df_evo['Mes_Num'].map(meses_nombres)
        
        fig_evo = px.line(df_evo, x='Mes', y=col_nps_puntaje, markers=True, title="Evolución NPS Promedio")
        st.plotly_chart(fig_evo, use_container_width=True)
        
        fig_bar_evo = px.bar(df_evo, x='Mes', y=col_fecha_nombre, text=col_fecha_nombre, title="Volumen de Encuestas por Mes")
        st.plotly_chart(fig_bar_evo, use_container_width=True)

    # ==========================================
    # TAB 4: ANÁLISIS DE RECLAMOS (LÓGICA SEMÁNTICA)
    # ==========================================
    with tab4:
        st.header("🔍 Auditoría de Comentarios y Reclamos")
        if len(df_mes) > 0:
            def clasificar_comentario(row):
                nota, texto = row[col_nps_puntaje], str(row[col_t_concatenado]).lower()
                # Limpieza de patrones automáticos
                limpio = re.sub(r"sí, fue entregado en la fecha acordada ✔️|no, pero fui informado del retraso ⚠️|sí|no|nan|-+|\d+|✔️|⚠️", "", texto).strip()
                
                # LISTA DE ELOGIOS (Fuerza "Conforme")
                elogios = ["atencion", "atención", "muy buena", "buena", "excelente", "gracias", "recomendado", "conforme", "impecable", "bien", "todo bien", "perfecto", "javier", "gutierrez", "servicio", "agradecido"]
                
                # LISTA DE QUEJAS (Fuerza "Oportunidad")
                dolores = ["mejorar", "sala", "espera", "demora", "tardó", "baño", "baños", "falta", "anticipado", "diferencia", "color", "revisar", "alineado", "precio", "caro"]

                if nota <= 6:
                    return "⚠️ Reclamo Crítico"
                elif nota >= 9:
                    # Prioridad 1: Si hay una palabra de "dolor", es oportunidad
                    if any(d in limpio for d in dolores):
                        return "💡 OPORTUNIDAD DE MEJORA"
                    # Prioridad 2: Si el texto es muy corto o contiene elogios claros, es CONFORME
                    if len(limpio) < 6 or any(e in limpio for e in elogios):
                        return "✅ CONFORME"
                    return "💡 OPORTUNIDAD DE MEJORA"
                return "Neutral"

            df_mes['Categoría'] = df_mes.apply(clasificar_comentario, axis=1)
            
            c_izq, c_der = st.columns([1, 2], gap="large")
            with c_izq:
                # Contadores para las métricas
                prom_total = len(df_mes[df_mes['Categoría'].str.contains("CONFORME|OPORTUNIDAD")])
                rec_total = len(df_mes[df_mes['Categoría'] == "⚠️ Reclamo Crítico"])
                
                m1, m2 = st.columns(2)
                with m1:
                    if st.button("🟢 VER PROMOTORES", key="t4_btn_p"): st.session_state.tab4_filter = "P"; st.rerun()
                    st.metric("Total Promotores", prom_total)
                with m2:
                    if st.button("🔴 VER RECLAMOS", key="t4_btn_r"): st.session_state.tab4_filter = "R"; st.rerun()
                    st.metric("Total Reclamos", rec_total)
                
                if st.session_state.tab4_filter:
                    if st.button("🔄 MOSTRAR TODO"): st.session_state.tab4_filter = None; st.rerun()

                st.write("---")
                # Gráfico circular de distribución
                df_pie = df_mes[df_mes['Categoría'] != "Neutral"]
                fig_pie_t4 = px.pie(df_pie, names='Categoría', hole=0.5, color='Categoría',
                                    color_discrete_map={"⚠️ Reclamo Crítico": "#dc3545", "✅ CONFORME": "#198754", "💡 OPORTUNIDAD DE MEJORA": "#ffc107"})
                st.plotly_chart(fig_pie_t4, use_container_width=True)

            with c_der:
                st.subheader("Listado Detallado de Feedback")
                if st.session_state.tab4_filter == "P":
                    df_final_t4 = df_mes[df_mes['Categoría'].str.contains("CONFORME|OPORTUNIDAD")]
                elif st.session_state.tab4_filter == "R":
                    df_final_t4 = df_mes[df_mes['Categoría'] == "⚠️ Reclamo Crítico"]
                else:
                    df_final_t4 = df_mes[df_mes['Categoría'] != "Neutral"]

                # MOSTRAR DATA POR FIN SIN CORTAR
                st.dataframe(
                    df_final_t4[[col_cliente, 'Categoría', col_nps_puntaje, col_t_concatenado]].rename(
                        columns={col_nps_puntaje: "Nota NPS", col_t_concatenado: "Comentario Completo del Cliente"}
                    ),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Comentario Completo del Cliente": st.column_config.TextColumn(width="large"),
                        "Categoría": st.column_config.TextColumn(width="medium")
                    },
                    height=650
                )
else:
    st.error("No se detectó el archivo de origen. Verifique la URL de Google Sheets.")
