import streamlit as st
import pandas as pd

# 1. Configuración de Diseño
st.set_page_config(
    page_title="Dashboard Calidad Cenoa",
    page_icon="📊",
    layout="wide",
)

# Título Principal
st.title("🚀 Principales Indicadores de Calidad - Taller Cenoa")
st.markdown("---")

# 2. Conexión de Datos
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

df = load_data()

if df is not None:
    # Buscador inteligente de columna NPS
    col_nps = next((c for c in df.columns if "escala" in c.lower() or "satisfecho" in c.lower()), None)
    
    if col_nps:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])

        # Cálculos de Indicadores
        total = len(df)
        promotores = len(df[df[col_nps] >= 9])
        detractores = len(df[df[col_nps] <= 6])
        pasivos = len(df[(df[col_nps] >= 7) & (df[col_nps] <= 8)])
        
        nps_score = ((promotores - detractores) / total) * 100
        csat_score = df[col_nps].mean()

        # --- SECCIÓN 1: MÉTRICAS DESTACADAS ---
        st.subheader("📊 Indicadores Clave de Desempeño")
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.metric(
                label="NPS (Net Promoter Score)",
                value=f"{int(nps_score)} pts",
                delta="🎯 Objetivo: > 70",
                help="Fórmula: %Promotores - %Detractores"
            )
            
        with m2:
            st.metric(
                label="CSAT (Satisfacción Media)",
                value=f"{csat_score:.2f} / 10",
                help="Promedio de todas las notas recibidas."
            )
            st.progress(csat_score / 10)
            
        with m3:
            st.metric(
                label="Total de Encuestas",
                value=total,
                help="Volumen total de respuestas procesadas."
            )

        st.markdown("---")

        # --- SECCIÓN 2: ANÁLISIS VISUAL ---
        col_izq, col_der = st.columns(2)

        with col_izq:
            st.markdown("### 📈 Distribución de Notas")
            # Conteo de notas del 1 al 10
            counts = df[col_nps].value_counts().sort_index()
            st.bar_chart(counts, color="#29b5e8")

        with col_der:
            st.markdown("### 👥 Segmentación de Clientes")
            df_segmentos = pd.DataFrame({
                "Categoría": ["Promotores", "Pasivos", "Detractores"],
                "Total": [promotores, pasivos, detractores]
            })
            st.bar_chart(df_segmentos, x="Categoría", y="Total", color="#FF4B4B")

        # --- SECCIÓN 3: TABLA DETALLADA ---
        st.markdown("---")
        with st.expander("🔍 Ver detalle de todas las respuestas"):
            st.dataframe(df, use_container_width=True)

    else:
        st.error("❌ No se encontró la columna de puntuación en el archivo.")
else:
    st.warning("⚠️ Sin datos para mostrar.")
