import streamlit as st
import pandas as pd

st.set_page_config(page_title="CALIDAD TALLER CENOA", layout="wide")
st.title("📊 ENCUESTAS DE SATISFACCIÓN")

# URL directa al CSV
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
    # --- BUSCADOR AUTOMÁTICO DE COLUMNA NPS ---
    # Buscamos cualquier columna que hable de satisfacción o escala del 1 al 10
    col_nps = None
    for c in df.columns:
        if "escala del 1 al 10" in c.lower() or "satisfecho" in c.lower():
            col_nps = c
            break
    
    if col_nps:
        # Limpieza de datos
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        total = len(df)
        
        if total > 0:
            prom = len(df[df[col_nps] >= 9])
            det = len(df[df[col_nps] <= 6])
            pas = len(df[(df[col_nps] >= 7) & (df[col_nps] <= 8)])
            nps_val = ((prom - det) / total) * 100
            
            # Mostrar métricas en grande
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("NPS Global", f"{int(nps_val)}")
            c2.metric("Promotores", prom)
            c3.metric("Pasivos", pas)
            c4.metric("Detractores", det)
            
            st.subheader("Distribución de Satisfacción")
            # Crear un gráfico de barras simple
            st.bar_chart(df[col_nps].value_counts().sort_index())
        else:
            st.warning("No hay datos numéricos en la columna de satisfacción.")
    else:
        st.error("No se encontró la columna de satisfacción. Verifica los títulos en tu Excel.")
    
    st.subheader("Vista previa de respuestas")
    st.write(df)
