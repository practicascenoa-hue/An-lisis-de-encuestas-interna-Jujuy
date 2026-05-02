import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="DASHBOARD POSTVENTA", layout="wide")

# Inicializar estados de filtro y resaltado
if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
if "f_val" not in st.session_state: st.session_state.f_val = None

# --- CSS: ESTILO CON RESALTADO DINÁMICO ---
def get_button_style(button_key):
    """Genera CSS para resaltar el botón seleccionado"""
    if st.session_state.get("last_clicked") == button_key:
        return f"""
            <style>
            div[data-testid="stHorizontalBlock"] div:nth-child(n) button[key="{button_key}"] {{
                background-color: #e7f3ff !important;
                border: 2px solid #007bff !important;
                color: #0056b3 !important;
                font-weight: bold !important;
            }}
            </style>
        """
    return ""

st.markdown("""
    <style>
    div.stButton > button {
        width: 100% !important;
        height: 38px !important;
        border-radius: 8px !important;
        border: 1px solid #dee2e6 !important;
        background-color: white !important;
        color: #495057 !important;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }
    .stPlotlyChart { margin-bottom: -60px !important; }
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
    col_seguimiento = df_raw.columns[15] # P
    col_comentario_K = df_raw.columns[10] # K
    col_ambiente = df_raw.columns[9]      # J
    col_nps_puntaje = df_raw.columns[16]  # Q
    col_csi_final = df_raw.columns[18]    # S
    col_nps_comentario = df_raw.columns[17] # R
    col_com_atencion = df_raw.columns[8]  # I
    col_com_calidad = df_raw.columns[12]  # M
    col_com_tiempo = df_raw.columns[14]   # O
    col_cliente = next((c for c in df_raw.columns if "nombre" in c.lower() and "apellido" in c.lower()), "Cliente")
    col_asesor = next((c for c in df_raw.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), "Asesor")

    def clean_val(x):
        try: return float(str(x).replace('%', '').replace(',', '.').strip())
        except: return 0.0

    df_mes[col_nps_puntaje] = df_mes[col_nps_puntaje].apply(clean_val)
    df_mes[col_csi_final] = df_mes[col_csi_final].apply(clean_val)
    df_mes[col_ambiente] = df_mes[col_ambiente].apply(clean_val)

    st.title("INDICADORES ENCUESTAS DE SATISFACCIÓN")
    tab1, tab2, tab3 = st.tabs(["🎯 INDICADORES", "👤 ASESORES", "📊 EVOLUCIÓN MENSUAL"])

    with tab1:
        if len(df_mes) > 0:
            nps_val = df_mes[col_nps_puntaje].mean() * 10
            csi_raw = df_mes[col_csi_final].mean()
            csi_val = csi_raw * 100 if csi_raw <= 1.1 else csi_raw
            amb_val = df_mes[col_ambiente].mean() * 10

            c1, c2 = st.columns(2)
            
            def crear_gauge(valor, titulo):
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=valor,
                    title={'text': f"<b>{titulo}</b>", 'font': {'size': 18}},
                    number={'valueformat': ".1f", 'suffix': "%", 'font': {'size': 40}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#34495e", 'thickness': 0.25},
                           'steps': [{'range': [0, 60], 'color': "#f8d7da"}, {'range': [60, 90], 'color': "#fff3cd"}, {'range': [90, 100], 'color': "#d1e7dd"}]}
                ))
                fig.update_layout(height=280, margin=dict(l=30, r=30, t=80, b=20), paper_bgcolor='rgba(0,0,0,0)')
                return fig

            with c1:
                st.plotly_chart(crear_gauge(nps_val, "NPS (Recomendación)"), use_container_width=True)
                p_c = len(df_mes[df_mes[col_nps_puntaje] >= 9])
                d_c = len(df_mes[df_mes[col_nps_puntaje] <= 6])
                pas_c = len(df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)])
                
                b1, b2, b3 = st.columns(3)
                if b1.button(f"🟢 {p_c} Prom", key="p_prom"):
                    st.session_state.update({"f_tipo":"NPS","f_val":"Promotor", "last_clicked":"p_prom"})
                if b2.button(f"🟡 {pas_c} Neu", key="p_neu"):
                    st.session_state.update({"f_tipo":"NPS","f_val":"Pasivo", "last_clicked":"p_neu"})
                if b3.button(f"🔴 {d_c} Det", key="p_det"):
                    st.session_state.update({"f_tipo":"NPS","f_val":"Detractor", "last_clicked":"p_det"})

            with c2:
                st.plotly_chart(crear_gauge(csi_val, "CSI (Satisfacción)"), use_container_width=True)
                limit = 90 if csi_val > 15 else 9
                exc_c = len(df_mes[df_mes[col_csi_final] >= limit])
                mal_c = len(df_mes[df_mes[col_csi_final] <= (limit-30 if limit==90 else 6)])
                reg_c = len(df_mes) - exc_c - mal_c
                
                b4, b5, b6 = st.columns(3)
                if b4.button(f"🟢 {exc_c} Exc", key="c_exc"):
                    st.session_state.update({"f_tipo":"CSI","f_val":"Excelente", "last_clicked":"c_exc"})
                if b5.button(f"🟡 {reg_c} Reg", key="c_reg"):
                    st.session_state.update({"f_tipo":"CSI","f_val":"Regular", "last_clicked":"c_reg"})
                if b6.button(f"🔴 {mal_c} Mal", key="c_mal"):
                    st.session_state.update({"f_tipo":"CSI","f_val":"Malo", "last_clicked":"c_mal"})

            # Inyectar CSS dinámico para resaltar el botón seleccionado
            if "last_clicked" in st.session_state:
                st.markdown(f"""
                    <style>
                    button[kind="secondary"]:has(div:contains("{st.session_state.f_val}")) {{
                        background-color: #e7f3ff !important;
                        border: 2px solid #007bff !important;
                        box-shadow: 0 0 10px rgba(0,123,255,0.2) !important;
                    }}
                    </style>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 12px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center; width: 100%; margin-top: 35px;">
                    <span style="color: #495057; font-size: 15px; font-weight: bold;">🏢 SATISFACCIÓN AMBIENTE TALLER: </span>
                    <span style="color: #2c3e50; font-size: 22px; font-weight: bold; margin-left: 8px;">{amb_val:.1f}%</span>
                </div>
            """, unsafe_allow_html=True)

            with st.expander(f"💬 Comentarios Generales de {mes_sel_nombre}"):
                for com in df_mes[col_comentario_K].dropna().unique():
                    if str(com).strip(): st.markdown(f"- {com}")
            
            if st.session_state.f_tipo:
                st.divider()
                st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
                if st.session_state.f_tipo == "NPS":
                    if st.session_state.f_val == "Promotor": df_f = df_mes[df_mes[col_nps_puntaje] >= 9]
                    elif st.session_state.f_val == "Detractor": df_f = df_mes[df_mes[col_nps_puntaje] <= 6]
                    else: df_f = df_mes[(df_mes[col_nps_puntaje] > 6) & (df_mes[col_nps_puntaje] < 9)]
                    cols = [col_cliente, col_asesor, col_nps_puntaje, col_nps_comentario]
                else:
                    if st.session_state.f_val == "Excelente": df_f = df_mes[df_mes[col_csi_final] >= limit]
                    elif st.session_state.f_val == "Malo": df_f = df_mes[df_mes[col_csi_final] <= (limit-30 if limit==90 else 6)]
                    else: df_f = df_mes[(df_mes[col_csi_final] < limit) & (df_mes[col_csi_final] > (limit-30 if limit==90 else 6))]
                    cols = [col_cliente, col_asesor, col_csi_final, col_com_atencion, col_com_calidad, col_com_tiempo]
                
                st.dataframe(df_f[cols].fillna("Sin comentario"), use_container_width=True)

    # ... (Resto de pestañas Asesores y Evolución se mantienen igual)
    with tab2:
        st.subheader(f"Desempeño de Asesores - {mes_sel_nombre}")
        if len(df_mes) > 0:
            df_as = df_mes.groupby(col_asesor).size().reset_index(name='Encuestas')
            st.plotly_chart(px.bar(df_as, x=col_asesor, y='Encuestas', text='Encuestas', color='Encuestas', color_continuous_scale='Blues'), use_container_width=True)
            st.markdown("---")
            ca, cb = st.columns([1, 2])
            with ca:
                res_p = df_mes[col_seguimiento].fillna("N/C").value_counts().reset_index()
                st.plotly_chart(px.pie(res_p, names=res_p.columns[0], values='count', hole=0.4), use_container_width=True)
            with cb:
                df_mes['Sigue_Num'] = df_mes[col_seguimiento].apply(lambda x: 1 if str(x).lower().strip() == 'sí' else 0)
                df_res = df_mes.groupby(col_asesor).agg(Total_Encuestas=(col_asesor, 'size'), Recibio_Seg_Count=('Sigue_Num', 'sum')).reset_index()
                df_res['% Cumplimiento'] = (df_res['Recibio_Seg_Count'] / df_res['Total_Encuestas'] * 100).round(1).astype(str) + "%"
                df_res['¿RECIBIÓ SEGUIMIENTO?'] = df_res['Recibio_Seg_Count'].apply(lambda x: "Sí" if x > 0 else "No")
                df_final = df_res[[col_asesor, 'Total_Encuestas', '¿RECIBIÓ SEGUIMIENTO?', '% Cumplimiento']]
                df_final.columns = ['Nombre de tu Asesor de Taller:', 'TOTAL ENCUESTAS', '¿RECIBIÓ SEGUIMIENTO?', '% Cumplimiento']
                st.dataframe(df_final.sort_values('TOTAL ENCUESTAS', ascending=False), use_container_width=True)

    with tab3:
        st.subheader(f"Evolución Mensual {anio_sel}")
        df_anio[col_csi_final] = df_anio[col_csi_final].apply(clean_val)
        df_anio[col_nps_puntaje] = df_anio[col_nps_puntaje].apply(clean_val)
        df_v = df_anio.groupby('Mes_Num').agg({col_fecha_nombre: 'count', col_csi_final: 'mean', col_nps_puntaje: lambda x: x.mean() * 10}).reset_index()
        df_v.columns = ['Mes_Num', 'Cant', 'CSI', 'NPS']
        df_v['Mes'] = df_v['Mes_Num'].map(meses_dict)
        fig_bar = px.bar(df_v, y='Mes', x='Cant', orientation='h', text='Cant', color='Cant', color_continuous_scale='Sunset')
        fig_bar.update_layout(yaxis={'categoryorder':'array', 'categoryarray':list(meses_dict.values())[::-1]}, height=500, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.error("No se pudieron cargar los datos.")
