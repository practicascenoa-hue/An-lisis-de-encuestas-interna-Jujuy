# --- DENTRO DE LA SECCIÓN DE TABLA DE AUDITORÍA ---
if st.session_state.f_tipo and st.session_state.f_val:
    col_target = 'Seg_NPS' if st.session_state.f_tipo == "NPS" else 'Seg_CSI'
    df_final = df[df[col_target] == st.session_state.f_val].copy()
    
    # Definimos las columnas: Agregamos el puntaje real de la Columna T (CSI)
    # para que puedas ver ese "56,67" al lado de los comentarios.
    cols_v = [
        col_cliente, 
        col_asesor, 
        col_csi,             # <--- AGREGAMOS EL VALOR PARTICULAR (Columna T)
        col_coment_atencion, 
        col_coment_calidad,  
        col_coment_tiempo,   
        col_coment_final     
    ]
    
    # Limpieza de nombres de columnas para que se vean bien en la tabla
    cols_v = [c for c in cols_v if c in df.columns]
    
    st.subheader(f"Auditoría Detallada: {st.session_state.f_val}")
    
    # Ordenar la tabla para que los valores más bajos aparezcan primero si es auditoría CSI
    if st.session_state.f_tipo == "CSI":
        df_final = df_final.sort_values(by=col_csi, ascending=True)

    st.dataframe(df_final[cols_v], use_container_width=True)
