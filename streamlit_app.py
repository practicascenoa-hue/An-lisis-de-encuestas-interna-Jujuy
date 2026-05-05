with tab4:
        st.header("⚠️ Análisis de Reclamos vs. Promotores (NPS)")
        
        if len(df_mes) > 0:
            # 1. Definición de Segmentos NPS
            df_mes['Segmento_NPS'] = df_mes[col_nps_puntaje].apply(
                lambda x: 'Promotor' if x >= 9 else ('Reclamo' if x <= 6 else 'Pasivo')
            )
            
            # Contadores para los botones
            cant_promotores = len(df_mes[df_mes['Segmento_NPS'] == 'Promotor'])
            cant_reclamos = len(df_mes[df_mes['Segmento_NPS'] == 'Reclamo'])

            # 2. Botones Funcionales Superiores
            c_btn1, c_btn2 = st.columns(2)
            
            with c_btn1:
                # Estilo Verde para Promotores
                st.markdown("""<style>
                    button[key="btn_prom"] { background-color: #d1e7dd !important; color: #0f5132 !important; border: 1px solid #badbcc !important; font-weight: bold; }
                    button[key="btn_prom_active"] { background-color: #198754 !important; color: white !important; font-weight: bold; }
                </style>""", unsafe_allow_html=True)
                
                is_active = st.session_state.get("tab4_filter") == "Promotor"
                if st.button(f"🟢 VER PROMOTORES ({cant_promotores})", key="btn_prom_active" if is_active else "btn_prom"):
                    st.session_state.tab4_filter = "Promotor"
                    st.rerun()

            with c_btn2:
                # Estilo Rojo para Reclamos
                st.markdown("""<style>
                    button[key="btn_recl"] { background-color: #f8d7da !important; color: #842029 !important; border: 1px solid #f5c2c7 !important; font-weight: bold; }
                    button[key="btn_recl_active"] { background-color: #dc3545 !important; color: white !important; font-weight: bold; }
                </style>""", unsafe_allow_html=True)
                
                is_active = st.session_state.get("tab4_filter") == "Reclamo"
                if st.button(f"🔴 VER RECLAMOS ({cant_reclamos})", key="btn_recl_active" if is_active else "btn_recl"):
                    st.session_state.tab4_filter = "Reclamo"
                    st.rerun()

            # 3. Gráfico de Torta (Resumen del Mes)
            st.divider()
            df_pie = df_mes[df_mes['Segmento_NPS'].isin(['Promotor', 'Reclamo'])]
            if not df_pie.empty:
                resumen_pie = df_pie['Segmento_NPS'].value_counts().reset_index()
                resumen_pie.columns = ['Tipo', 'Cantidad']
                
                fig_torta = px.pie(
                    resumen_pie, 
                    values='Cantidad', 
                    names='Tipo',
                    hole=0.5,
                    color='Tipo',
                    color_discrete_map={'Promotor': '#198754', 'Reclamo': '#dc3545'},
                    title="Distribución General: Promotores vs Reclamos"
                )
                fig_torta.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_torta, use_container_width=True)
            
            # 4. Mostrar Información Filtrada
            current_filter = st.session_state.get("tab4_filter")
            if current_filter:
                st.subheader(f"Detalle de clientes: {current_filter}es")
                df_filtrado = df_mes[df_mes['Segmento_NPS'] == current_filter]
                
                # Columna T (Concatenado) para ver el motivo completo
                col_t_concatenado = df_raw.columns[19] 
                
                cols_mostrar = [col_cliente, col_asesor, col_nps_puntaje, col_t_concatenado]
                st.dataframe(
                    df_filtrado[cols_mostrar].rename(columns={col_t_concatenado: "Comentario / Concatenado (Col T)"}), 
                    use_container_width=True, 
                    hide_index=True
                )
        else:
            st.warning("No hay datos suficientes para generar el análisis en este periodo.")
