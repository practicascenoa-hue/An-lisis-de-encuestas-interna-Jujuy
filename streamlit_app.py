def crear_gauge(valor, titulo):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(valor, 1),
        title={'text': f"<b>{titulo}</b>", 'font': {'size': 20, 'color': '#2c3e50'}},
        number={'font': {'size': 48, 'family': "Arial", 'color': '#2c3e50'}, 'suffix': "%" if "CSI" in titulo else ""},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#ced4da", 'ticklen': 5},
            'bar': {'color': "#34495e", 'thickness': 0.25}, # Barra principal oscura
            'bgcolor': "white",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 60], 'color': "#f8d7da"},   # Rojo muy suave
                {'range': [60, 90], 'color': "#fff3cd"},  # Amarillo muy suave
                {'range': [90, 100], 'color': "#d1e7dd"}  # Verde muy suave
            ],
            'threshold': {
                'line': {'color': "#2c3e50", 'width': 4},
                'thickness': 0.75,
                'value': valor
            }
        }
    ))
    
    fig.update_layout(
        height=250, 
        margin=dict(l=60, r=60, t=80, b=0),
        paper_bgcolor='rgba(0,0,0,0)', # Fondo transparente
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig
