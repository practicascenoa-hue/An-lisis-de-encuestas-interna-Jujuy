import streamlit as st
import pandas as pd
import plotly.express as px # Recomendado para gráficos interactivos

# ... (Mantener el código anterior de carga de datos) ...

try:
    df = load_data()
    
    st.header("Análisis Detallado de Satisfacción")

    # 1. Definimos el nombre exacto de la columna (Cópialo tal cual aparece en tu Sheet)
    pregunta_turno = "Cuán satisfecho estuvo con la facilidad para obtener un turno que se adapte a sus necesidades?"

    if pregunta_turno in df.columns:
        st.subheader("Indicador: Facilidad de Turnos")
        
        # Limpieza: Asegurarnos de que los valores sean numéricos
        df[pregunta_turno] = pd.to_numeric(df[pregunta_turno], errors='coerce')
        df = df.dropna(subset=[pregunta_turno])

        # Cálculos de métricas
        promedio_turno = df[pregunta_turno].mean()
        max_valor = 5 # Cambia a 10 si tu escala es del 1 al 10
        satisfaccion_pct = (promedio_turno / max_valor) * 100

        # Mostrar métricas en columnas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Promedio", f"{promedio_turno:.2f} / {max_valor}")
        with col2:
            st.metric("% Satisfacción", f"{satisfaccion_pct:.1f}%")
        with col3:
            total_votos = len(df[pregunta_turno])
            st.metric("Total Respuestas", total_votos)

        # 2. Gráfico de distribución para esta pregunta
        st.write("Distribución de calificaciones:")
        conteo_votos = df[pregunta_turno].value_counts().sort_index().reset_index()
        conteo_votos.columns = ['Calificación', 'Cantidad']
        
        fig = px.bar(conteo_votos, x='Calificación', y='Cantidad', 
                     color='Cantidad', color_continuous_scale='RdYlGn',
                     text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(f"No se encontró la columna: {pregunta_turno}. Revisa los encabezados de tu Sheet.")

except Exception as e:
    st.error(f"Error procesando indicadores: {e}")
