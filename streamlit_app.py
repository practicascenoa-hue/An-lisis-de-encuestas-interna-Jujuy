import streamlit as st
import pandas as pd

# 1. Configuración básica
st.set_page_config(page_title="Dashboard Calidad Cenoa", layout="wide")

# Título del Portal
st.title("🚀 Dashboard de Calidad Cenoa (NPS & CSAT)")
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
    # --- BUSCADOR AUTOMÁTICO DE COLUMNA DE SATISFACCIÓN ---
    # Buscamos la columna que contenga "escala" o "satisfecho"
    col_nps = next((c for c in df.columns if "escala" in c.lower() or "satisfecho" in c.lower()), None)

    if col_nps:
        # Limpieza de datos: Convertimos a número y quitamos vacíos
        df[col_nps] = pd.to_numeric(df[col_nps], errors='coerce')
        df = df.dropna(subset=[col_nps])
        
        total = len(df)
        
        if total > 0:
            # Cálculos de indicadores
            prom = len(df[df[col_nps] >= 9])
            det = len(df[df[col_nps] <= 6])
            pas = len(df[(df[col_nps] >= 7) & (df[col_nps] <= 8)])
            
            nps_val = ((prom - det) / total) * 100
            csat_val = df[col_nps].mean()

            # --- VISTA AMIGABLE (Métricas) ---
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("NPS Global", f"{int(nps_val)} pts")
                st.info("🎯 Objetivo: > 70")
            with c2:
                st.metric("CSAT (Promedio)", f"{csat_val:.2f} / 10")
                st.progress(csat_val / 10)
            with c3:
                st.metric("Total Respuestas", total)
                st.write("✅ Datos actualizados")

            st.markdown("---")

            # --- GRÁFICOS ---
            col_izq, col_der = st.columns(2)
            
            with col_izq:
                st.subheader("📊 Distribución de Clientes")
                labels = ["Promotores (9-10)", "Pasivos (7-8)", "Detractores (0-6)"]
                valores = [prom, pas, det]
                # Gráfico de barras simple pero efectivo
                st.bar_chart(pd.DataFrame({"Cantidad": valores}, index=labels))

            with col_der:
                st.subheader("📈 Frecuencia de Notas")
                # Histograma de las notas del 1 al 10
                notas_count = df[col_nps].value_counts().sort_index()
                st.area_chart(notas_count)

        else:
            st.warning("Se encontró la columna, pero no hay datos numéricos aún.")
    else:
        st.error("No se detectó la columna de satisfacción. Revisa los títulos en el Excel.")
    
    # Vista de tabla al final
    with st.expander("Ver Base de Datos Completa"):
        st.write(df)

else:
    st.error("No se pudo conectar con la fuente de datos.")
