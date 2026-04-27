import streamlit as st
import pandas as pd

# 1. Configuración de Diseño (Ancho completo)
st.set_page_config(
    page_title="Dashboard NPS Cenoa",
    page_icon="📊",
    layout="wide",
)

# Título Principal del Dashboard
st.title("🚀 Principales Indicadores de Calidad - Taller Cenoa")
st.markdown("---")

# 2. Conexión de Datos (Pública)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600) # Se actualiza cada 10 min
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

df = load_data()

if df is not None:
    # --- Identificación Automática de Columnas ---
    # Buscamos la columna de la escala 1-10 (NPS)
    col_nps = next((c for c in df.columns if "escala" in c.lower() or "satisfecho" in c.lower()), None)
    
    if col_nps:
        # Limpieza de datos (asegurar números)
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])

        # --- Cálculos de Indicadores ---
        total = len(df)
        promotores = len(df[df[col_nps] >= 9])
        detractores = len(df[df[col_nps] <= 6])
        
        # NPS (Net Promoter Score)
        nps_score = ((promotores - detractores) / total) * 100
        
        # CSAT (Customer Satisfaction Score) - Promedio
        csat_score = df[col_nps].mean()

        # --- SECCIÓN 1: MÉTRICAS DESTACADAS (Al estilo de tu imagen) ---
        st.subheader("Indicadores Clave de Desempeño")
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.metric(
                label="NPS (Net Promoter Score)",
                value=f"{int(nps_score)} pts",
                delta="🎯 Objetivo: > 70",
                help="Porcentaje de Promotores (9-10) menos porcentaje de Detractores (0-6)."
            )
            
        with m2:
            st.metric(
                label="CSAT (Satisfacción Promedio)",
                value=f"{csat_val:.2f} / 10",
                help="Promedio simple de todas las notas recibidas del 1 al 10."
            )
            # Pequeña barra visual de progreso para CSAT
            st.progress(csat_val / 10)
            
        with m3:
            st.metric(
                label="Total de Encuestas",
                value=total,
                help="Volumen total de respuestas válidas analizadas."
            )

        st.markdown("---")

        # --- SECCIÓN 2: GRÁFICOS VISUALES ---
        st.subheader("Análisis Detallado de Feedback")
        col_izq, col_der = st.columns([1, 1])

        with col_izq:
            st.markdown("### Distribución de Notas (Frecuencia)")
            # Gráfico de barras automático para las notas del 1 al 10
            counts = df[col_nps].value_counts().sort_index()
            st.bar_chart(counts, color="#29b5e8")

        with col_der:
            st.markdown("### Categorías de Clientes (NPS)")
            # Gráfico de área para ver la tendencia de notas
            st.area_chart(counts)

        # --- SECCIÓN 3: TABLA DE DATOS ---
        st.markdown("---")
        with st.expander("🔍 Ver detalle de todas las respuestas"):
            st.dataframe(df, use_container_width=True)

    else:
        st.error("❌ No se encontró la columna de puntuación (1-10) en tu Google Sheet.")
else:
    st.warning("⚠️ Esperando datos...")
