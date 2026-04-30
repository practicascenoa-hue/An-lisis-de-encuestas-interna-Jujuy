import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# Estilos de botones
st.markdown("""
    <style>
    div.stButton > button { width: 100%; height: 85px; border-radius: 12px; border: none; color: white; font-weight: bold; font-size: 16px; }
    .stColumn:nth-of-type(1) div.stButton > button { background-color: #28a745; } 
    .stColumn:nth-of-type(2) div.stButton > button { background-color: #ffc107; color: #212529; } 
    .stColumn:nth-of-type(3) div.stButton > button { background-color: #dc3545; } 
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
    except:
        return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    # Filtros de Fecha
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                  7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    st.sidebar.header("⚙️ Control de Reporte")
    anios_disponibles = sorted(df_raw['Año'].dropna().unique().astype(int), reverse=True)
    anio_sel = st.sidebar.selectbox("Año", anios_disponibles)
    
    meses_nros = sorted(df_raw[df_raw['Año'] == anio_sel]['Mes_Num'].dropna().unique().astype(int))
    mes_sel_nombre = st.sidebar.selectbox("Mes", [meses_dict[m] for m in meses_nros])
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    # Filtrado principal
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # Identificación de columnas (H=7, L=11, N=13, Q=17, T=19)
    col_nps = next((c for c in df.columns if "recomiendes" in c.lower()), None)
    col_csi = df.columns[19] if len(df.columns) > 19 else None
    col_h = df.columns[7]; col_l = df.columns[11]; col_n = df.columns[13]
    col_cliente = next((c for c in df.columns if "nombre" in c.lower() and "apellido" in c.lower()), None)
    col_asesor = next((c for c in df.columns if "asesor" in c.lower() or "recepcionista" in c.lower()), None)
    col_comentario = df.columns[17]

    st.title("🚀 Dashboard de Calidad Cenoa")

    if len(df) > 0:
        # Limpieza agresiva de datos numéricos
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        # Para el CSI: si viene como "80%", lo limpia y lo vuelve número
        if col_csi:
            df[col_csi] = df[col_csi].astype(str).str.replace('%', '').str.replace(',', '.')
            df[col_csi] = pd.to_numeric(df[col_csi], errors='coerce')

        # --- LOGICA NPS ---
        df_nps = df.dropna(subset=[col_nps])
        nps_val = 0; p_c = 0; pas_c = 0; d_c = 0
        if not df_nps.empty:
            df['Seg_NPS'] = df[col_nps].apply(lambda x: 'Promotor' if x >= 9 else ('Detractor' if x <= 6 else 'Pasivo' if pd.notna(x) else None))
            p_c = len(df[df['Seg_NPS']=='Promotor'])
            pas_c = len(df[df['Seg_NPS']=='Pasivo'])
            d_c = len(df[df['Seg_NPS']=='Detractor'])
            nps_val = ((p_c - d_c) / len(df_nps)) * 100

        # --- LOGICA CSI ---
        csi_val = 0; exc_c = 0; reg_c = 0; mal_c = 0
        if col_csi:
            df_csi_valid = df.dropna(subset=[col_csi])
            if not df_csi_valid.empty:
                # Normalizar: si el máximo es <= 1, asumimos que es porcentaje (0.8 -> 80)
                media_csi = df_csi_valid[col_csi].mean()
                csi_val = media_csi * 100 if df_csi_valid[col_csi].max() <= 1.1 else media_csi
                
                # Clasificación (asumiendo escala 1-10 o 1-100)
                def clasificar_csi(x):
                    if pd.isna(x): return None
                    val = x * 10 if x <= 1.1 else x
                    return 'Excelente' if val >= 90 or (val >= 9 and val <= 10) else ('Malo' if val <= 60 or val <= 6 else 'Regular')
                
                df['Seg_CSI'] = df[col_csi].apply(clasificar_csi)
                exc_c = len(df[df['Seg_CSI']=='Excelente'])
                reg_c = len(df[df['Seg_CSI']=='Regular'])
                mal_c = len(df[df['Seg_CSI']=='Malo'])

        # --- INTERFAZ ---
        if "f_tipo" not in st.session_state: st.session_state.f_tipo = None
        if "f_val" not in st.session_state: st.session_state.f_val = None

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=nps_val, title={'text': "NPS Recomendación"}, gauge={'axis': {'range': [-100, 100]}, 'bar': {'color': "black"}, 'steps': [{'range': [-100, 0], 'color': "#FF4B4B"}, {'range': [0, 70], 'color': "#FFA500"}, {'range': [70, 100], 'color': "#00CC96"}]})), use_container_width=True)
            st.write("🔍 **Auditar NPS:**")
            b1, b2, b3 = st.columns(3)
            if b1.button(f"PROMOTORES\n({p_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Promotor"
            if b2.button(f"PASIVOS\n({pas_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Pasivo"
            if b3.button(f"DETRACTORES\n({d_c})"): st.session_state.f_tipo = "NPS"; st.session_state.f_val = "Detractor"

        with c2:
            st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=csi_val, title={'text': "CSI Unificado (Col. T)"}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "black"}, 'steps': [{'range': [0, 70], 'color': "#FF4B4B"}, {'range': [70, 85], 'color': "#FFA500"}, {'range': [85, 100], 'color': "#00CC96"}]})), use_container_width=True)
            st.write("🔍 **Auditar CSI:**")
            bc1, bc2, bc3 = st.columns(3)
            if bc1.button(f"EXCELENTE\n({exc_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Excelente"
            if bc2.button(f"REGULAR\n({reg_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Regular"
            if bc3.button(f"MALO\n({mal_c})"): st.session_state.f_tipo = "CSI"; st.session_state.f_val = "Malo"

        st.markdown("---")
        # Mostrar tabla solo si hay un filtro seleccionado y la columna existe en el dataframe
        if st.session_state.f_tipo and st.session_state.f_val:
            col_busqueda = 'Seg_NPS' if st.session_state.f_tipo == "NPS" else 'Seg_CSI'
            
            if col_busqueda in df.columns:
                df_final = df[df[col_busqueda] == st.session_state.f_val].copy()
                cols_v = [c for c in [col_cliente, col_asesor, col_h, col_l, col_n, col_comentario] if c]
                st.subheader(f"Auditoría {st.session_state.f_tipo}: {st.session_state.f_val}")
                st.dataframe(df_final[cols_v], use_container_width=True)
            else:
                st.warning("Selecciona un segmento con datos (ej. Promotores) para ver la tabla.")
    else:
        st.warning("No hay datos para este mes.")
