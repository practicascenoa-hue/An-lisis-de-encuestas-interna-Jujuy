import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="DASHBOARD POSTVENTA", layout="wide")

# Inicializar estados de filtro
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

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
    col_nps_comentario = df_raw.columns[17] # Columna R
    col_com_atencion = df_raw.columns[8]    # Columna I
    col_com_calidad = df_raw.columns[12]   # Columna M
    col_com_tiempo = df_raw.columns[14]    # Columna O
    col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Cliente")
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
    
    tab1, tab2 = st.tabs(["🎯 INDICADORES", "📊 EVOLUCIÓN MENSUAL"])

    with tab1:
        # Cálculos
        nps_f = df_mes[col_nps_puntaje].mean() * 10
        csi_raw = df_mes[col_csi_final].mean()
        csi_f = csi_raw * 100 if csi_raw <= 1.1 else csi_raw
        amb_f = df_mes[col_ambiente].mean() * 10

        # --- DISEÑO SUPERIOR: 2 GAUGES + KPI COMPACTO ---
        col_g1, col_kpi, col_g2 = st.columns([1.5, 1, 1.5])
        
        def draw_gauge(val, title):
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=val,
                title={'text': f"<b>{title}</b>", 'font': {'size': 18}},
                number={'valueformat': ".1f", 'suffix': "%", 'font': {'size': 40}},
                gauge={'axis': {'range': [0, 100]},
                       'bar': {'color': "#34495e", 'thickness': 0.25},
                       'steps': [{'range': [0, 60], 'color': "#f8d7da"},
                                 {'range': [60, 90], 'color': "#fff3cd"},
                                 {'range': [90, 100], 'color': "#d1e7dd"}]}
            ))
            fig.update_layout(height=260, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
            return fig

        with col_g1:
            st.plotly_chart(draw_gauge(nps_f, "NPS (Recomendación)"), use_container_width=True)
        
        with col_kpi:
            # Opción 2: KPI Compacto Estilizado
            st.markdown("<br>"*2, unsafe_allow_html=True)
            st.markdown(f"""
                <div style="background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #5D6D7E; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); text-align: center;">
                    <p style="color: #5D6D7E; font-size: 14px; font-weight: bold; margin-bottom: 5px;">🏢 AMBIENTE TALLER</p>
                    <h2 style="color: #2c3e50; margin: 0; font-size: 32px;">{amb_f:.1f}%</h2>
                    <p style="color: #aeb6bf; font-size: 12px; margin-top: 5px;">Satisfacción Instalaciones</p>
                </div>
            """, unsafe_allow_html=True)

        with col_g2:
            st.plotly_chart(draw_gauge(csi_f, "CSI (Servicio)"), use_container_width=True)

        st.divider()

        # --- BOTONES DE AUDITORÍA ---
        p_c = len(df_mes[df_mes[col_nps_puntaje] >= 9])
        d_c = len(df_mes[df_mes[col_nps_puntaje] <= 6])
        pas_c = len(df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)])
        
        limit = 90 if csi_f > 15 else 9
        exc_c = len(df_mes[df_mes[col_csi_final] >= limit])
        mal_c = len(df_mes[df_mes[col_csi_final] <= (limit-30 if limit==90 else 6)])
        reg_c = len(df_mes) - exc_c - mal_c

        st.write("### Auditoría de Calificaciones")
        b_col1, b_col2 = st.columns(2)
        
        with b_col1:
            st.write("**NPS:**")
            s1, s2, s3 = st.columns(3)
            s1.button(f"🟢 {p_c} Prom", key="p", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Promotor"}))
            s2.button(f"🟡 {pas_c} Neu", key="n", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo"}))
            s3.button(f"🔴 {d_c} Det", key="d", on_click=lambda: st.session_state.update({"f_tipo":"NPS","f_val":"Detractor"}))

        with b_col2:
            st.write("**CSI:**")
            s4, s5, s6 = st.columns(3)
            s4.button(f"🟢 {exc_c} Exc", key="e", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Excelente"}))
            s5.button(f"🟡 {reg_c} Reg", key="r", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Regular"}))
            s6.button(f"🔴 {mal_c} Mal", key="m", on_click=lambda: st.session_state.update({"f_tipo":"CSI","f_val":"Malo"}))

        if st.session_state.f_tipo:
            st.divider()
            st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
            if st.session_state.f_tipo == "NPS":
                if st.session_state.f_val == "Promotor": df_f = df_mes[df_mes[col_nps_puntaje] >= 9]
                elif st.session_state.f_val == "Detractor": df_f = df_mes[df_mes[col_nps_puntaje] <= 6]
                else: df_f = df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)]
                cols = [col_cliente, col_asesor, col_ambiente, col_nps_puntaje, col_nps_comentario]
            else:
                if st.session_state.f_val == "Excelente": df_f = df_mes[df_mes[col_csi_final] >= limit]
                elif st.session_state.f_val == "Malo": df_f = df_mes[df_mes[col_csi_final] <= (limit-30 if limit==90 else 6)]
                else: df_f = df_mes[(df_mes[col_csi_final] < limit) & (df_mes[col_csi_final] > (limit-30 if limit==90 else 6))]
                cols = [col_cliente, col_asesor, col_ambiente, col_csi_final, col_com_atencion, col_com_calidad, col_com_tiempo]
            
            st.dataframe(df_f[cols].fillna("Sin comentarios"), use_container_width=True)

    with tab2:
        st.subheader(f"Evolución Mensual {anio_sel}")
        df_anio[col_csi_final] = df_anio[col_csi_final].apply(clean_val)
        df_anio[col_nps_puntaje] = df_anio[col_nps_puntaje].apply(clean_val)
        
        df_v = df_anio.groupby('Mes_Num').agg({col_fecha_nombre: 'count', col_csi_final: 'mean', col_nps_puntaje: lambda x: x.mean() * 10}).reset_index()
        df_v.columns = ['Mes_Num', 'Cant', 'CSI', 'NPS']
        df_v['Mes'] = df_v['Mes_Num'].map(meses_dict)

        fig = px.bar(df_v, y='Mes', x='Cant', orientation='h', text='Cant', color='Cant', color_continuous_scale='Sunset',
                     hover_data={'CSI': ':.1f', 'NPS': ':.1f'})
        fig.update_layout(yaxis={'categoryorder':'array', 'categoryarray':list(meses_dict.values())[::-1]}, height=500, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("No se pudo cargar la información del Google Sheet.")
