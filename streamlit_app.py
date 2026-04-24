import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portal de Calidad Cenoa", layout="wide")
st.title("📊 Portal de Calidad Cenoa")

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
    # NOMBRE EXACTO DE TU COLUMNA (Copiado de tu imagen)
    col_nps = "En una escala del 1 al 10, donde 1 es terrible y 10 es excelente ¿Cuán satisfecho estuvo con la facilidad para obtener un turno que se adapte a sus necesidades?:"
    
    # Si esa columna existe en el archivo
    if col_nps in df.columns:
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        total = len(df)
        
        if total > 0:
            prom = len(df[df[col_nps] >= 9])
            det = len(df[df[col_nps] <= 6])
            pas = len(df[(df[col_nps] >= 7) & (df[col_nps] <= 8)])
            nps_val = ((prom - det) / total) * 100
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("NPS Global", f"{int(nps_val)}")
            c2.metric("Promotores", prom)
            c3.metric("Pasivos", pas)
            c4.metric("Detractores", det)
            
            st.subheader("Distribución de Notas")
            st.bar_chart(df[col_nps].value_counts().sort_index())
        else:
            st.warning("Hay respuestas, pero no tienen números todavía.")
    else:
        st.error("Aún no detecto la columna de notas. Revisa que el nombre sea idéntico.")
    
    st.subheader("Base de Datos Completa")
    st.write(df)
