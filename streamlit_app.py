import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Dashboard de Satisfacción - Cenoa", layout="wide")

st.title("📊 Portal de Monitoreo NPS - Taller Cenoa")

# URL de tu Google Sheet convertido a formato CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data
def load_data():
    # Cargamos los datos
    df = pd.read_csv(SHEET_URL)
    return df

try:
    df = load_data()

    # --- LÓGICA DE NPS ---
    # Asumiendo que existe una columna llamada 'Puntuación' o 'Recomendación' (escala 0-10)
    # Si el nombre es distinto, cámbialo aquí:
    col_puntuacion = 'Puntuación' 

    if col_puntuacion in df.columns:
        total_respuestas = len(df)
        promotores = len(df[df[col_puntuacion] >= 9])
        detractores = len(df[df[col_puntuacion] <= 6])
        pasivos = len(df[(df[col_puntuacion] == 7) | (df[col_puntuacion] == 8)])

        nps = ((promotores - detractores) / total_respuestas) * 100

        # Mostrar métricas principales
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("NPS Total", f"{int(nps)}")
        col2.metric("Promotores (9-10)", f"{promotores}")
        col3.metric("Pasivos (7-8)", f"{pasivos}")
        col4.metric("Detractores (0-6)", f"{detractores}")

        # Gráfico de barras simple
        st.subheader("Distribución de Feedback")
        chart_data = pd.DataFrame({
            'Categoría': ['Promotores', 'Pasivos', 'Detractores'],
            'Cantidad': [promotores, pasivos, detractores]
        })
        st.bar_chart(data=chart_data, x='Categoría', y='Cantidad')
    else:
        st.warning(f"No se encontró la columna '{col_puntuacion}'. Por favor, verifica el nombre en tu Google Sheet.")

    # Mostrar tabla de datos
    with st.expander("Ver base de datos completa"):
        st.write(df)

except Exception as e:
    st.error(f"Error al conectar con los datos: {e}")
