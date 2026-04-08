import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Portal de Satisfacción", layout="wide")

st.title("📊 Indicadores de Satisfacción")

# --- 1. DEFINICIÓN DE LA FUNCIÓN (Esto es lo que falta) ---
@st.cache_data
def load_data():
    sheet_id = "1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y"
    sheet_name = "Resp.%20de%20form.%20de%20Satisf."
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    return df

# --- 2. EJECUCIÓN Y CÁLCULOS ---
try:
    # Aquí llamamos a la función
    data = load_data()
    
    st.header("Análisis Detallado de Satisfacción")

    # Nombre exacto de la columna de tu Sheet
    pregunta_turno = "Cuán satisfecho estuvo con la facilidad para obtener un turno que se adapte a sus necesidades?"

    if pregunta_turno in data.columns:
        # Convertir a numérico por si hay errores
        data[pregunta_turno] = pd.to_numeric(data[pregunta_turno], errors='coerce')
        df_limpio = data.dropna(subset=[pregunta_turno])

        # Métricas
        promedio = df_limpio[pregunta_turno].mean()
        col1, col2 = st.columns(2)
        col1.metric("Puntaje Promedio", f"{promedio:.2f} / 5")
        col2.metric("Total Respuestas", len(df_limpio))

        # Gráfico
        fig = px.histogram(df_limpio, x=pregunta_turno, 
                           title="Distribución de Respuestas",
                           nbins=5, 
                           color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"No se encontró la columna. Columnas disponibles: {list(data.columns)}")

except Exception as e:
    st.error(f"Error procesando indicadores: {e}")
