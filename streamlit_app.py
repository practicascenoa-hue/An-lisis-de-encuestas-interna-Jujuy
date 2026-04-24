import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="NPS - Planificación Taller Cenoa",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Portal de Satisfacción y NPS")
st.markdown("---")

# URL de exportación directa (formato CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ER40wQho6sPz24oBvEUmQnsHnAxrnzmP3ppPukMy24Y/export?format=csv&gid=309618647"

@st.cache_data(ttl=600) # Se actualiza cada 10 minutos
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Limpieza básica: eliminar filas vacías
        df = df.dropna(how='all')
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return None

df = load_data()

if df is not None:
    # --- Identificación de Columnas ---
    # Basado en tu archivo, buscamos la columna de puntuación. 
    # Si el nombre exacto es "Puntuación", "Calificación" o similar, la buscamos:
    posibles_nombres = ['Puntuación', 'NPS', 'Calificación', '¿Qué nota nos pones?', 'Puntaje']
    col_nps = next((c for c in posibles_nombres if c in df.columns), df.columns[0])

    # Convertir a numérico por si hay textos
    df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
    df = df.dropna(subset=[col_nps])

    # --- Cálculos de NPS ---
    total_respuestas = len(df)
    promotores = len(df[df[col_nps] >= 9])
    detractores = len(df[df[col_nps] <= 6])
    pasivos = len(df[(df[col_nps] >= 7) & (df[col_nps] <= 8)])

    if total_respuestas > 0:
        nps_score = ((promotores - detractores) / total_respuestas) * 100
    else:
        nps_score = 0

    # --- Interfaz de Métricas ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NPS Global", f"{int(nps_score)}")
    c2.metric("👍 Promotores", f"{promotores}", f"{int(promotores/total_respuestas*100)}%")
    c3.metric("😐 Pasivos", f"{pasivos}", f"{int(pasivos/total_respuestas*100)}%")
    c4.metric("👎 Detractores", f"{detractores}", f"{int(detractores/total_respuestas*100)}%")

    st.markdown("---")

    # --- Gráficos ---
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("Distribución de Categorías")
        dist_data = pd.DataFrame({
            'Categoría': ['Promotores', 'Pasivos', 'Detractores'],
            'Cantidad': [promotores, pasivos, detractores]
        })
        st.bar_chart(data=dist_data, x='Categoría', y='Cantidad', color='#29b5e8')

    with col_der:
        st.subheader("Histórico de Respuestas")
        # Si tienes una columna de fecha, la usamos para un gráfico de líneas
        col_fecha = next((c for c in ['Marca temporal', 'Fecha'] if c in df.columns), None)
        if col_fecha:
            df[col_fecha] = pd.to_datetime(df[col_fecha])
            df_fecha = df.groupby(df[col_fecha].dt.date)[col_nps].count()
            st.line_chart(df_fecha)
        else:
            st.info("No se encontró columna de fecha para el gráfico histórico.")

    # --- Tabla de Datos ---
    st.subheader("Detalle de Encuestas")
    st.dataframe(df, use_container_width=True)

else:
    st.stop()
