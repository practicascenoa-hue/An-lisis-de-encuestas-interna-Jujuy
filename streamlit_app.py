import streamlit as st
import pandas as pd

st.set_page_config(page_title="ENCUESTAS", layout="wide")

st.title("📊 Medición de Satisfacción Cliente")

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
    # 1. Buscamos la columna de puntuación (NPS)
    # Buscamos nombres comunes: Puntuación, Nota, Puntaje, etc.
    col_objetivo = None
    for col in df.columns:
        if any(palabra in col.lower() for palabra in ['punt', 'nota', 'nps', 'recomienda']):
            col_objetivo = col
            break
    
    if col_objetivo:
        # Convertimos a números y quitamos lo que no sea número
        df[col_objetivo] = pd.to_numeric(df[col_objetivo], errors='coerce')
        df = df.dropna(subset=[col_objetivo])
        
        total = len(df)
        
        if total > 0:
            promotores = len(df[df[col_objetivo] >= 9])
            detractores = len(df[df[col_objetivo] <= 6])
            pasivos = len(df[(df[col_objetivo] >= 7) & (df[col_objetivo] <= 8)])
            nps = ((promotores - detractores) / total) * 100
            
            # Mostrar métricas
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("NPS Global", f"{int(nps)}")
            c2.metric("Promotores", promotores)
            c3.metric("Pasivos", pasivos)
            c4.metric("Detractores", detractores)
            
            st.bar_chart(df[col_objetivo].value_counts().sort_index())
        else:
            st.warning("⚠️ No hay datos numéricos en la columna detectada.")
    else:
        st.error("❌ No encontré una columna de puntuación (ej: 'Puntuación').")
        st.write("Columnas disponibles en tu archivo:", df.columns.tolist())

    # Mostrar la tabla para revisar qué está llegando
    st.subheader("Vista previa de los datos")
    st.write(df)
else:
    st.error("No se pudo conectar con Google Sheets.")
