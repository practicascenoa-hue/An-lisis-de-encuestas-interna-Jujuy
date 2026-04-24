import streamlit as st
import pandas as pd

# 1. Configuración de Estilo
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# CSS personalizado para mejorar el diseño
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🚀 Dashboard de Calidad y Satisfacción")
st.markdown("---")

# 2. Carga de Datos
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.dropna(how='all')
    except:
        return None

df = load_data()

if df is not None:
    # Buscador automático de columna de notas
    col_nps = next((c for c in df.columns if "escala del 1 al 10" in c.lower() or "satisfecho" in c.lower()), None)

    if col_nps:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        
        # Cálculos
        total = len(df)
        prom = len(df[df[col_nps] >= 9])
        det = len(df[df[col_nps] <= 6])
        pas = len(df[(df[col_nps] >= 7) & (df[col_nps] <= 8)])
        nps_val = ((prom - det) / total) * 100
        csat_val = df[col_nps].mean() # El promedio de todas las notas

        # --- FILA 1: MÉTRICAS PRINCIPALES ---
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.metric("NPS (Net Promoter Score)", f"{int(nps_val)} pts")
            st.caption("Fórmula: %Promotores - %Detractores")
            
        with m2:
            st.metric("CSAT (Satisfacción Media)", f"{csat_val:.2f} / 10")
            st.progress(csat_val / 10)
            
        with m3:
            st.metric("Total Respuestas", f"{total} encuestas")
            st.caption("Volumen total de feedback recibido")

        st.markdown("---")

        # --- FILA 2: GRÁFICOS ---
        g1, g2 = st.columns([1, 1])

        with g1:
            st.subheader("📊 Distribución por Categoría")
            # Crear DataFrame para el gráfico de torta/dona
            df_pie = pd.DataFrame({
                "Categoría": ["Promotores (9-10)", "Pasivos (7-8)", "Detractores (0-6)"],
                "Cant": [prom, pas, det]
            })
            st.bar_chart(data=df_pie, x="Categoría", y="Cant", color="#29b5e8")

        with g2:
            st.subheader("📈 Tendencia de Notas")
            counts = df[col_nps].value_counts().sort_index()
            st.area_chart(counts)

        # --- FILA 3: TABLA DETALLADA ---
        st.markdown("---")
        with st.expander("🔍 Ver detalle de todas las respuestas"):
            st.dataframe(df, use_container_width=True)
            
    else:
        st.error("No se encontró la columna de satisfacción en el Excel.")
else:
    st.error("No se pudo conectar con la base de datos.")
