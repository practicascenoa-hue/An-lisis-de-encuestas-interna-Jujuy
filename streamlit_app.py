import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portal de Satisfacción", layout="wide")

st.title("📊 Indicadores de Satisfacción")

# Configuración de la URL de Google Sheets
# Nota: Convertimos la URL normal en una URL de exportación CSV
sheet_id = "1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y"
sheet_name = "Resp.%20de%20form.%20de%20Satisf." # El nombre de la hoja con codificación URL
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

@st.cache_data
def load_data():
    df = pd.read_csv(url)
    return df

try:
    data = load_data()
    
    # --- Filtros en la barra lateral ---
    st.sidebar.header("Filtros")
    # Ejemplo: Si tienes una columna llamada 'Fecha' o 'Sucursal'
    # sucursal = st.sidebar.multiselect("Selecciona Sucursal", options=data["Sucursal"].unique())

    # --- Visualización de Datos ---
    st.write("Datos recientes de la encuesta:")
    st.dataframe(data.head())

    # --- Ejemplo de Métrica ---
    if not data.empty:
        total_respuestas = len(data)
        st.metric("Total de Encuestas", total_respuestas)
        
        # Aquí puedes agregar gráficos como:
        # st.bar_chart(data["Calificación"].value_counts())

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.info("Asegúrate de que el Google Sheet esté compartido como 'Cualquier persona con el enlace'.")
