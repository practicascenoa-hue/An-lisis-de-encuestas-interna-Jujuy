import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="NPS - Cenoa", page_icon="📊", layout="wide")

st.title("📊 Portal de Satisfacción y NPS")

# URL de exportación directa
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df = df.dropna(how='all') # Eliminar filas totalmente vacías
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

df = load_data()

if df is not None:
    # Intentamos encontrar la columna de puntaje (NPS suele ser del 1 al 10)
    # Buscamos columnas que contengan 'Punt' o 'Nota' o 'NPS'
    col_nps = None
    for c in df.columns:
        if any(keyword in c.lower() for keyword in ['punt', 'nota', 'nps', 'recomienda']):
            col_nps = c
            break
    
    # Si no la encuentra, usamos la primera columna numérica que veamos
    if not col_nps:
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            col_nps = numeric_cols[0]

    if col_nps:
        # Limpiamos datos no numéricos
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        
        total = len(df)
        
        if total > 0:
            promotores = len(df[df[col_nps] >= 9])
            detractores = len(df[df[col_nps] <= 6])
            pasivos = len(df[(df[col_nps] >= 7) & (df[col_nps] <= 8)])
            
            nps_score = ((promotores - detractores) / total) * 100
            
            # Métricas con protección contra división por cero
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("NPS Global", f"{int(nps_score)}")
            c2.metric("👍 Promotores", f"{promotores}", f"{int((promotores/total)*100)}%")
            c3.metric("😐 Pasivos", f"{pasivos}", f"{int((pasivos/total)*100)}%")
            c4.metric("👎 Detractores", f"{detractores}", f"{int((detractores/total)*100)}%")
            
            st.bar_chart(df[col_nps].value_counts().sort_index())
        else:
            st.warning("Se encontró la columna, pero no hay datos numéricos (puntuaciones) todavía.")
    else:
        st.error("No pudimos identificar la columna de puntuación. Verifica que el Google Sheet tenga una columna llamada 'Puntuación'.")
        st.write("Columnas detectadas:", df.columns.tolist())

    st.subheader("Datos actuales")
    st.dataframe(df)
