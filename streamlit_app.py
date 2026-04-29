import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# --- CARGA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Forzamos la búsqueda de "Marca temporal"
        col_fecha = "Marca temporal"
        
        if col_fecha in df.columns:
            # Convertimos a fecha asegurando que el formato sea el correcto
            df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
            # Eliminamos filas donde la fecha no se pudo procesar
            df = df.dropna(subset=[col_fecha])
        else:
            st.error(f"No se encontró la columna '{col_fecha}' en el archivo.")
            return None, None
            
        return df.dropna(how='all'), col_fecha
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None, None

df_raw, col_fecha_nombre = load_data()

if df_raw is not None:
    # --- PROCESAMIENTO DE FILTROS ---
    df_raw['Año'] = df_raw[col_fecha_nombre].dt.year.astype(int)
    df_raw['Mes_Num'] = df_raw[col_fecha_nombre].dt.month.astype(int)
    
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                  7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.header("⚙️ Filtros de Control")
    
    # 1. Selector de Año
    anios_disponibles = sorted(df_raw['Año'].unique().tolist(), reverse=True)
    anio_sel = st.sidebar.selectbox("Seleccione el Año", anios_disponibles)
    
    # 2. Selector de Mes (Dependiente del año)
    df_anio = df_raw[df_raw['Año'] == anio_sel]
    meses_disponibles_num = sorted(df_anio['Mes_Num'].unique().tolist())
    meses_nombres = [meses_dict[m] for m in meses_disponibles_num]
    
    mes_sel_nombre = st.sidebar.selectbox("Seleccione el Mes", meses_nombres)
    
    # Obtener el número del mes seleccionado
    mes_sel_num = [k for k, v in meses_dict.items() if v == mes_sel_nombre][0]
    
    # Filtrar el DataFrame final para los cálculos
    df = df_raw[(df_raw['Año'] == anio_sel) & (df_raw['Mes_Num'] == mes_sel_num)].copy()

    # --- CUERPO PRINCIPAL ---
    st.title("🚀 Dashboard de Calidad Cenoa")
    st.info(f"📅 Datos de {mes_sel_nombre} {anio_sel} (Fuente: {col_fecha_nombre})")

    # Identificar columna NPS (Pregunta principal de recomendación)
    col_nps = next((c for c in df.columns if "escala" in c.lower() or "satisfecho" in c.lower()), None)
    
    if col_nps and len(df) > 0:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        total = len(df)
        
        if total > 0:
            promotores = len(df[df[col_nps] >= 9])
            detractores = len(df[df[col_nps] <= 6])
            nps_score = ((promotores - detractores) / total) * 100
            csat_score = df[col_nps].mean()

            # --- RELOJES ---
            c1, c2 = st.columns(2)
            with c1:
                fig_nps = go.Figure(go.Indicator(
                    mode = "gauge+number", value = nps_score, title = {'text': "NPS Global"},
                    gauge = {'axis': {'range': [-100, 100]}, 'bar': {'color': "black"},
                             'steps': [{'range': [-100, 0], 'color': "#FF4B4B"},
                                       {'range': 0, 70], 'color': "#FFA500"},
                                       {'range': 70, 100], 'color': "#00CC96"}]}))
                st.plotly_chart(fig_nps, use_container_width=True)
            with c2:
                fig_csat = go.Figure(go.Indicator(
                    mode = "gauge+number", value = csat_score, title = {'text': "CSAT (Promedio)"},
                    gauge = {'axis': {'range': [0, 10]}, 'bar': {'color': "black"},
                             'steps': [{'range': [0, 6], 'color': "#FF4B4B"},
                                       {'range': [6, 8.5], 'color': "#FFA500"},
                                       {'range': [8.5, 10], 'color': "#00CC96"}]}))
                st.plotly_chart(fig_csat, use_container_width=True)

            # --- SECCIÓN DE ANÁLISIS POR PILARES ---
            st.markdown("---")
            st.header("🔍 Análisis por Pilares de Calidad")
            cp1, cp2, cp3 = st.columns(3)

            # Mapeo de columnas por palabras clave
            col_rep = next((c for c in df.columns if any(x in c.lower() for x in ["chapa", "pintura", "calidad del trabajo"])), None)
            col_tie = next((c for c in df.columns if any(x in c.lower() for x in ["acordada", "fecha", "entrega"])), None)
            col_ate = next((c for c in df.columns if any(x in c.lower() for x in ["explicaron", "factura", "atención"])), None)

            with cp1:
                st.subheader("🛠️ Calidad Reparación")
                if col_rep:
                    # Calculamos notas 9 y 10 para reparación de chapa
                    exitos = len(df[pd.to_numeric(df[col_rep], errors='coerce') >= 9])
                    pct = (exitos / total) * 100
                    st.metric("Indice Chapa y Pintura", f"{int(pct)}%")
                    st.progress(pct/100)
                else: st.warning("Columna Chapa/Pintura no hallada")

            with cp2:
                st.subheader("⏰ Tiempo")
                if col_tie:
                    si_t = len(df[df[col_tie].astype(str).str.lower().str.contains("si|sí")])
                    pct_t = (si_t / total) * 100
                    st.metric("Cumplimiento Entrega", f"{int(pct_t)}%")
                    st.progress(pct_t/100)
                else: st.warning("Columna Tiempo no hallada")

            with cp3:
                st.subheader("📞 Atención")
                if col_ate:
                    si_a = len(df[df[col_ate].astype(str).str.lower().str.contains("si|sí")])
                    pct_a = (si_a / total) * 100
                    st.metric("Claridad Factura", f"{int(pct_a)}%")
                    st.progress(pct_a/100)
                else: st.warning("Columna Atención no hallada")
        else:
            st.warning(f"No hay suficientes respuestas numéricas en {mes_sel_nombre}.")
    else:
        st.warning(f"No hay datos registrados en {mes_sel_nombre} {anio_sel}.")
else:
    st.error("No se pudo cargar el archivo desde Google Sheets.")
