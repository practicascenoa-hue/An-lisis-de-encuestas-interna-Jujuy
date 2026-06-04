import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
 
# 1. Configuración de página
st.set_page_config(page_title="DASHBOARD POSTVENTA", layout="wide")
 
# Inicializar estados de sesión para filtros y botones
if "f_tipo" not in st.session_state:
    st.session_state.f_tipo = None
if "f_val" not in st.session_state:
    st.session_state.f_val = None
if "btn_active" not in st.session_state:
    st.session_state.btn_active = None
if "tab4_filter" not in st.session_state:
    st.session_state.tab4_filter = None
 
# --- CSS: ESTILO GLOBAL Y TARJETAS DINÁMICAS ---
st.markdown("""
     <style>
     div.stButton > button {
         width: 100% !important;
         height: 38px !important;
         border-radius: 8px !important;
     }
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
     
     /* TARJETAS CON IDENTIDAD DE COLOR PARA LECTURA COMPLETA */
     .comentario-card {
        background-color: #ffffff;
         padding: 15px;
         border-radius: 8px;
         margin-bottom: 10px;
         box-shadow: 0 2px 8px rgba(0,0,0,0.05);
         border: 1px solid #eee;
     }
     .borde-conforme { border-left: 5px solid #28a745; }
     .borde-oportunidad { border-left: 5px solid #ffc107; }
     .borde-critico { border-left: 5px solid #dc3545; }
     
     .comentario-header { font-weight: bold; color: #333; margin-bottom: 5px; font-size: 14px; }
     .comentario-body { color: #555; font-size: 13px; line-height: 1.5; }
 
     /* FORZAR SALTO DE LÍNEA EN TABLAS Y DATAFRAMES */
     [data-testid="stTable"] td, [data-testid="stDataFrame"] td {
         white-space: normal !important;
         word-break: break-word !important;
         line-height: 1.4 !important;
     }
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
     # --- MAPEADO DE COLUMNAS ---
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
     col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Cliente")
     col_asesor = next((c for c in df_raw.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")
 
     # --- LIMPIEZA DE DATOS ---
     def clean_val(x):
         if pd.isna(x): return 0.0
         try:
             val = str(x).replace('%', '').replace(',', '.').strip()
             return float(val)
         except: return 0.0
 
     df_raw[col_nps_puntaje] = df_raw[col_nps_puntaje].apply(clean_val)
     df_raw[col_csi_final] = df_raw[col_csi_final].apply(clean_val)
     df_raw[col_ambiente_J] = df_raw[col_ambiente_J].apply(clean_val)
 
     # Sidebar: Filtros de Tiempo
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
 
     st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")
     tab1, tab2, tab3, tab4 = st.tabs(["🎯 INDICADORES", "👤 ASESORES", "📊 EVOLUCIÓN MENSUAL", "⚠️ ANÁLISIS DE RECLAMOS"])
 
     # --- TAB 1: INDICADORES (CON RESUMEN EJECUTIVO DE ALTO IMPACTO) ---
     with tab1:
         st.header(f"🎯 Indicadores Clave - {mes_sel_nombre} {anio_sel}")
                 
         if len(df_mes) > 0:
             # --- 1. SECCIÓN SUPERIOR: KPIs GLOBALES (NPS & CSI) ---
             st.markdown("### Resumen Ejecutivo")
             
             # Cálculos base globales
             nps_val = df_mes[col_nps_puntaje].mean() * 10
             csi_raw = df_mes[col_csi_final].mean()
             csi_val = csi_raw * 100 if csi_raw <= 1.1 else csi_raw
 
             # Determinar etiquetas y colores según el rendimiento
             def obtener_status_kpi(valor):
                 if valor >= 90: return "Excelente 🟢", "#28a745"
                 elif valor >= 60: return "Regular 🟡", "#ffc107"
                 return "Crítico 🔴", "#dc3545"
 
             status_nps, color_nps = obtener_status_kpi(nps_val)
             status_csi, color_csi = obtener_status_kpi(csi_val)
 
             c1, c2 = st.columns(2)
             
             with c1:
                 # Tarjeta de Diseño para NPS
                 st.markdown(f"""
                     <div style="background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid {color_nps}; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px;">
                         <span style="color: #6c757d; font-size: 14px; font-weight: bold; text-transform: uppercase;">Métrica de Recomendación</span>
                         <h2 style="color: #2c3e50; margin: 5px 0 0 0; font-size: 38px; font-weight: bold;">NPS: {nps_val:.1f}%</h2>
                         <p style="color: {color_nps}; font-weight: bold; margin: 2px 0 15px 0; font-size: 15px;">Estado: {status_nps}</p>
                         <div style="background-color: #e9ecef; border-radius: 4px; height: 8px; width: 100%; margin-bottom: 10px;">
                             <div style="background-color: {color_nps}; height: 8px; border-radius: 4px; width: {min(max(nps_val, 0), 100)}%;"></div>
                         </div>
                     </div>
                     """, unsafe_allow_html=True)
                 
                 # Conteo para botones de auditoría
                 p_c = len(df_mes[df_mes[col_nps_puntaje] >= 9])
                 d_c = len(df_mes[df_mes[col_nps_puntaje] <= 6])
                 pas_c = len(df_mes) - p_c - d_c
                 
                 b1, b2, b3 = st.columns(3)
                 if b1.button(f"🟢 {p_c} Promotores", key="btn1_nps"):
                     st.session_state.update({"f_tipo":"NPS","f_val":"Promotor"}); st.rerun()
                 if b2.button(f"🟡 {pas_c} Pasivos", key="btn2_nps"):
                     st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo"}); st.rerun()
                 if b3.button(f"🔴 {d_c} Detractores", key="btn3_nps"):
                     st.session_state.update({"f_tipo":"NPS","f_val":"Detractor"}); st.rerun()
 
             with c2:
                 # Tarjeta de Diseño para CSI
                 st.markdown(f"""
                     <div style="background-color: white; padding: 20px; border-radius: 12px; border-left: 6px solid {color_csi}; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px;">
                         <span style="color: #6c757d; font-size: 14px; font-weight: bold; text-transform: uppercase;">Índice de Satisfacción General</span>
                         <h2 style="color: #2c3e50; margin: 5px 0 0 0; font-size: 38px; font-weight: bold;">CSI: {csi_val:.1f}%</h2>
                         <p style="color: {color_csi}; font-weight: bold; margin: 2px 0 15px 0; font-size: 15px;">Estado: {status_csi}</p>
                         <div style="background-color: #e9ecef; border-radius: 4px; height: 8px; width: 100%; margin-bottom: 10px;">
                             <div style="background-color: {color_csi}; height: 8px; border-radius: 4px; width: {min(max(csi_val, 0), 100)}%;"></div>
                         </div>
                     </div>
                     """, unsafe_allow_html=True)
                 
                 # Conteo para botones de auditoría CSI
                 limit_exc = 90 if csi_val > 15 else 9
                 limit_mal = 60 if csi_val > 15 else 6
                 exc_c = len(df_mes[df_mes[col_csi_final] >= limit_exc])
                 mal_c = len(df_mes[df_mes[col_csi_final] <= limit_mal])
                 reg_c = len(df_mes) - exc_c - mal_c
                 
                 b4, b5, b6 = st.columns(3)
                 if b4.button(f"🟢 {exc_c} Excelentes", key="btn4_csi"):
                     st.session_state.update({"f_tipo":"CSI","f_val":"Excelente"}); st.rerun()
                 if b5.button(f"🟡 {reg_c} Regulares", key="btn5_csi"):
                     st.session_state.update({"f_tipo":"CSI","f_val":"Regular"}); st.rerun()
                 if b6.button(f"🔴 {mal_c} Malos", key="btn6_csi"):
                     st.session_state.update({"f_tipo":"CSI","f_val":"Malo"}); st.rerun()
 
             st.write("---")
             
             # --- 2. SECCIÓN INFERIOR: CUADRÍCULA DE ANILLOS LIMPIOS ---
             st.markdown("###  ")
             
             # --- FILA 1 DE ANILLOS (Preguntas 1, 2 y 3) ---
             cod1, cod2, cod3 = st.columns(3)
             
             with cod1:
                 col_f_turno = df_mes.columns[5]
                 st.plotly_chart(crear_anillo_corporativo(df_mes[col_f_turno], "Q5 - Facilidad de Agendamiento"), use_container_width=True, key="anillo_q5_agendamiento")
 
             with cod2:
                 col_h_asesor = df_raw.columns[7]
                 st.plotly_chart(crear_anillo_corporativo(df_mes[col_h_asesor], "Q8 - Cortesía y Competencia Asesor"), use_container_width=True, key="anillo_q8_asesor")
                     
             with cod3:
                 st.plotly_chart(crear_anillo_corporativo(df_mes[col_ambiente_J], "Q6 - Calidad Instalaciones y Confort"), use_container_width=True, key="anillo_q6_ambiente")
 
             st.write("") # Espacio sutil entre filas
 
             # --- FILA 2 DE ANILLOS (Preguntas 4 y 5) ---
             cod4, cod5, cod6 = st.columns(3)
 
             with cod4:
                 col_l_chapa = df_mes.columns[11]
                 st.plotly_chart(crear_anillo_corporativo(df_mes[col_l_chapa], "Q12 - Calidad Chapa y Pintura"), use_container_width=True, key="anillo_q12_chapa")
 
             with cod5:
                 col_n_tiempo = df_mes.columns[13]
                 st.plotly_chart(crear_anillo_corporativo(df_mes[col_n_tiempo], "Q9 - Tiempo de Reparación"), use_container_width=True, key="anillo_q9_tiempo")
 
             with cod6:
                 st.info("📊 **Siguiente pregunta disponible**\n\nEspacio libre en la segunda fila.")             
           
     # --- TAB 2: ASESORES ---
     with tab2:
        st.subheader(f"👤 Desempeño de Asesores - {mes_sel_nombre} {anio_sel}")
        
        if len(df_mes) > 0:
            # 1. Gráfico de volumen de encuestas por asesor
            df_as = df_mes.groupby(col_asesor).size().reset_index(name='Encuestas')
            st.plotly_chart(px.bar(df_as, x=col_asesor, y='Encuestas', text='Encuestas', color='Encuestas', color_continuous_scale='Blues'), use_container_width=True, key="bar_asesores_vol")
            
            st.markdown("---")
            
            ca, cb = st.columns([1, 2])
            
            with ca:
                # Gráfico de torta global de seguimiento en el mes
                res_p = df_mes[col_seguimiento].fillna("N/C").value_counts().reset_index()
                st.plotly_chart(px.pie(res_p, names=res_p.columns[0], values='count', hole=0.4), use_container_width=True, key="pie_seguimiento_global")
            
            with cb:
                # Aseguramos la limpieza de la columna Q8 (Cortesía - Columna H / Índice 7) de forma temporal para la tabla
                col_h_asesor = df_mes.columns[7]
                df_mes['Q8_Num'] = pd.to_numeric(df_mes[col_h_asesor], errors='coerce')
                
                # Lógica de conversión para el cumplimiento del seguimiento
                df_mes['Sigue_Num'] = df_mes[col_seguimiento].apply(lambda x: 1 if str(x).lower().strip() == 'sí' else 0)
                
                # Agrupación maestra por asesor sumando volumen, seguimiento y la nueva columna promedio Q8
                df_res = df_mes.groupby(col_asesor).agg(
                    Total_Encuestas=(col_asesor, 'size'),
                    Recibio_Seg_Count=('Sigue_Num', 'sum'),
                    Nota_Q8_Prom=('Q8_Num', 'mean') # <-- Tu columna extra estratégica
                ).reset_index()
                
                # Formateo de métricas para la visualización final de la tabla
                df_res['% Cumplimiento Seg.'] = (df_res['Recibio_Seg_Count'] / df_res['Total_Encuestas'] * 100).round(1).astype(str) + "%"
                df_res['Nota Cortesía (Q8)'] = df_res['Nota_Q8_Prom'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "Sin notas")
                
                # Columnas finales seleccionadas y ordenadas para el negocio
                columnas_finales = [
                    col_asesor, 
                    'Total_Encuestas', 
                    '% Cumplimiento Seg.', 
                    'Nota Cortesía (Q8)' # <-- Columna extra inyectada al final
                ]
                
                st.markdown("### 📊 Tabla de Rendimiento Individual")
                st.dataframe(
                    df_res[columnas_finales].sort_values('Total_Encuestas', ascending=False), 
                    use_container_width=True, 
                    hide_index=True
                )
 
     # --- TAB 3: EVOLUCIÓN (FIXED) ---
     with tab3:
        st.subheader(f"Evolución Mensual {anio_sel}")
        df_v = df_anio.groupby('Mes_Num').agg({col_fecha_nombre: 'count', col_csi_final: 'mean', col_nps_puntaje: 'mean'}).reset_index()
        df_v.columns = ['Mes_Num', 'Cant', 'CSI', 'NPS']
        df_v['NPS'] = df_v['NPS'] * 10
        df_v['Mes'] = df_v['Mes_Num'].map(meses_dict)
        st.plotly_chart(px.bar(df_v, y='Mes', x='Cant', orientation='h', text='Cant', color='Cant', color_continuous_scale='Sunset'), use_container_width=True)
 
# --- TAB 4: RECLAMOS (LÓGICA NPS ESTRICTA + CATEGORIZACIÓN ÚNICA) ---
     with tab4:
        # 1. Expander Informativo
        with st.expander("ℹ️ PROTOCOLO VOC (voz del cliente)"):
            st.markdown("""
            **Este panel clasifica las encuestas mediante un algoritmo de detección de palabras clave y jerarquía de NPS.**
            
            ### 1. El Semáforo de Gestión
            * 🔴 **Reclamo Crítico:** Clientes con **NPS ≤ 6**. Es una alerta de insatisfacción que requiere contacto inmediato.
            * 🟡 **Oportunidad de Mejora:** Clientes **Promotores (NPS 9-10)** que dejaron una sugerencia puntual sobre procesos.
            * 🟢 **Conforme:** Clientes **Promotores (NPS 9-10)** con comentarios 100% positivos o elogios directos.

            ### 2. Dimensiones de Calidad
            * **🛠️ Calidad Técnica:** Estado de la unidad, pintura, alineación y limpieza final.
            * **⏱️ Plazos y Tiempos:** Cumplimiento de fechas y tiempos de espera en sucursal.
            * **🏢 Infraestructura:** Comodidad de la sala, estado de baños y servicios (café/WiFi).
            * **👤 Atención y Trato:** Amabilidad, claridad técnica y calidad de comunicación del asesor.

            ### 3. Regla de Jerarquía Única
            Para evitar duplicar datos en el gráfico de barras, si un cliente menciona varios temas, el sistema prioriza el impacto operativo en este orden: 
            **1. Técnico > 2. Tiempos > 3. Infraestructura > 4. Atención.**
            """)

        st.header("⚠️ Análisis de Reclamos y Oportunidades")
        
        if len(df_mes) > 0:
            def clasificar_intencion(row):
                nota, texto = row[col_nps_puntaje], str(row[col_t_concatenado]).lower()
                elogios_fuertes = ["excelente", "muy buena", "impecable", "satisfecho", "gracias", "recomendadisimo", "perfecto", "todo bien", "todo el tiempo"]
                dolores = ["mejorar", "demora", "tardó", "falta", "sucio", "polvillo", "color", "alineado", "baño", "baños", "espera", "anticipado", "pero"]
                
                if nota <= 6: 
                    return "⚠️ RECLAMO CRÍTICO"
                elif nota >= 9:
                    if any(d in texto for d in dolores):
                        if any(e in texto for e in elogios_fuertes) and "pero" not in texto and "demoraron" not in texto:
                            return "✅ CONFORME"
                        return "💡 OPORTUNIDAD DE MEJORA"
                    return "✅ CONFORME"
                return "Neutral"
            
            df_mes['Intención'] = df_mes.apply(clasificar_intencion, axis=1)
            df_mes['Grupo'] = df_mes['Intención'].apply(lambda x: "Reclamos" if "RECLAMO" in x else ("Promotores" if x != "Neutral" else "Neutral"))
            cp, cr = len(df_mes[df_mes['Grupo'] == 'Promotores']), len(df_mes[df_mes['Grupo'] == 'Reclamos'])
            
            col_izq, col_der = st.columns([1, 2], gap="large")
            
            with col_izq:
                c_b1, c_b2 = st.columns(2)
                with c_b1:
                    if st.button("🟢 PROMOTORES", key="t4_p_final"):
                        st.session_state.tab4_filter = "Promotor"
                        st.rerun()
                    st.metric("", cp)
                with c_b2:
                    if st.button("🔴 RECLAMOS", key="t4_r_final"):
                        st.session_state.tab4_filter = "Reclamo"
                        st.rerun()
                    st.metric("", cr)
                
                if st.session_state.tab4_filter:
                    if st.button("🔄 Ver Todo", key="res_t4"):
                        st.session_state.tab4_filter = None
                        st.rerun()
                
                st.write("---")
                
                df_p = df_mes[df_mes['Grupo'] != "Neutral"]
                if not df_p.empty:
                    fig_p = px.pie(df_p, names='Grupo', hole=0.5, color='Grupo', color_discrete_map={"Reclamos": "#dc3545", "Promotores": "#198754"})
                    fig_p.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0), showlegend=False)
                    st.plotly_chart(fig_p, use_container_width=True)
                
                st.markdown("**🔍 Temas detectados por Gravedad:**")
                temas_prioridad = [
                    ("Calidad Técnica", ["color", "alineado", "ruido", "pintura", "sucio", "lavado"]),
                    ("Plazos y Tiempos", ["demora", "tardó", "fecha", "espera", "tiempo"]),
                    ("Infraestructura", ["sala", "baño", "café", "comodidad"]),
                    ("Atención", ["atencion", "atención", "trato", "explicación"])
                ]
                
                filas_b = []
                for _, row in df_mes.iterrows():
                    if row['Intención'] in ["⚠️ RECLAMO CRÍTICO", "💡 OPORTUNIDAD DE MEJORA"]:
                        texto_com = str(row[col_t_concatenado]).lower()
                        tema_asignado = None
                        for nom, keys in temas_prioridad:
                            if any(p in texto_com for p in keys):
                                tema_asignado = nom
                                break 
                        
                        if tema_asignado:
                            t = "Reclamo" if row['Intención'] == "⚠️ RECLAMO CRÍTICO" else "Oportunidad"
                            filas_b.append({"Tema": tema_asignado, "Tipo": t})

                if filas_b:
                    df_barras = pd.DataFrame(filas_b).groupby(['Tema', 'Tipo']).size().reset_index(name='Casos')
                    fig_b = px.bar(df_barras, x='Casos', y='Tema', orientation='h', color='Tipo', 
                                   color_discrete_map={"Reclamo": "#dc3545", "Oportunidad": "#FFD700"})
                    fig_b.update_layout(showlegend=True, height=350, margin=dict(t=10,b=10,l=0,r=10),
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    fig_b.update_traces(width=0.5)
                    st.plotly_chart(fig_b, use_container_width=True)

            with col_der:
                df_t = df_mes[df_mes['Grupo'] == "Promotores"] if st.session_state.tab4_filter == "Promotor" else (df_mes[df_mes['Grupo'] == "Reclamos"] if st.session_state.tab4_filter == "Reclamo" else df_mes[df_mes['Grupo'] != "Neutral"])
                st.subheader("Auditoría de Feedback Detallado")
                for _, row in df_t.iterrows():
                    cls = "borde-conforme" if row['Intención'] == "✅ CONFORME" else ("borde-oportunidad" if row['Intención'] == "💡 OPORTUNIDAD DE MEJORA" else "borde-critico")
                    st.markdown(f"""<div class="comentario-card {cls}"><div class="comentario-header">{row[col_cliente]} | {row['Intención']} | Nota: {row[col_nps_puntaje]}</div><div class="comentario-body">{row[col_t_concatenado]}</div></div>""", unsafe_allow_html=True)
            
        # Bloque final: Protocolo de Tratamiento
        st.markdown("---")
        st.subheader("📋 Protocolo de Tratamiento sugerido")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            st.info("""
            **🔴 RECLAMOS CRÍTICOS (Contención)**
            1. **Contacto:** Llamada del Jefe de Servicio en < 24hs.
            2. **Solución:** Ofrecer solución técnica o compensación.
            3. **Causa Raíz:** Identificar por qué falló el proceso.
            """)
        with col_act2:
            st.warning("""
            **🟡 OPORTUNIDADES (Mejora Continua)**
            1. **Análisis:** Revisar en reunión semanal de equipo.
            2. **Ajuste:** Modificar procesos internos o infraestructura.
            3. **Feedback:** Capacitación grupal basada en la sugerencia.
            """)
