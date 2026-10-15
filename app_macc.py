import streamlit as st # type: ignore
import pandas as pd # type: ignore
import plotly.graph_objects as go # type: ignore

# Configuración de la página
st.set_page_config(
    page_title="MACC Generator",
    page_icon="📉",  # Puedes poner un emoji o la ruta a un archivo .ico
    layout="wide"
)

st.title("📉 Generador de Curvas MACC")
st.markdown("Ingresa datos manualmente en la tabla o sube un Excel.")

# --- SECCIÓN 1: DATOS (MANUAL O EXCEL) ---

# Columnas base que necesitamos
columnas = ['Medida', 'Costo', 'Potencial']

# Crear un DataFrame de ejemplo para la plantilla
plantilla_data = {
    'Nombre Medida': ['Ejemplo 1', 'Ejemplo 2'],
    'Costo ($)': [-10, 20],
    'Potencial (tCO2)': [100, 50]
}
df_plantilla = pd.DataFrame(plantilla_data)

# Convertir a Excel en memoria
from io import BytesIO
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_plantilla.to_excel(writer, index=False, sheet_name='Hoja1')
    writer.close() # Importante cerrar el writer
    processed_data = output.getvalue()

st.download_button(
    label="📥 Descargar Plantilla Excel",
    data=processed_data,
    file_name="plantilla_macc.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Opción para subir archivo
archivo = st.file_uploader("📂 Importar Excel (Opcional)", type=['xlsx', 'xls'])

if archivo:
    # Si hay archivo, leemos los datos
    try:
        df_inicial = pd.read_excel(archivo)
        # Asegurarnos que tenga las columnas correctas, si no, renombramos o avisamos
        # Aquí asumimos que el usuario sube algo decente, pero filtramos columnas útiles
        df_inicial = df_inicial.iloc[:, :3] # Tomamos las 3 primeras columnas por defecto
        df_inicial.columns = columnas # Forzamos nombres para estandarizar
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        df_inicial = pd.DataFrame(columns=columnas)
else:
    # Si no hay archivo, creamos datos de ejemplo para que no esté vacío al inicio
    df_inicial = pd.DataFrame([
        {"Medida": "Ejemplo A", "Costo": -20, "Potencial": 50},
        {"Medida": "Ejemplo B", "Costo": 10, "Potencial": 30},
    ])

# --- SECCIÓN 2: TABLA EDITABLE (EL "EXCEL" EN PANTALLA) ---
st.info("💡 Puedes editar los valores directamente en esta tabla. El gráfico se actualizará solo.")

# num_rows="dynamic" permite agregar filas nuevas haciendo clic abajo
df = st.data_editor(
    df_inicial,
    column_config={
        "Costo": st.column_config.NumberColumn("Costo ($/tCO2)", format="$%.2f"),
        "Potencial": st.column_config.NumberColumn("Potencial (tCO2)", format="%d t"),
    },
    num_rows="dynamic",
    use_container_width=True
)

# --- SECCIÓN 3: CÁLCULOS MACC ---

# 1. FILTRADO DE SEGURIDAD (ESTA ES LA SOLUCIÓN)
# Eliminamos filas que tengan valores vacíos (NaN o None) en Costo o Potencial
# Así, mientras escribes la nueva fila, el código la ignora hasta que termines.
df_clean = df.dropna(subset=['Costo', 'Potencial'])

# Solo graficamos si hay datos válidos
if not df_clean.empty:
    
    # 2. Ordenar por Costo (Usamos df_clean en vez de df)
    df_sorted = df_clean.sort_values(by="Costo", ascending=True).reset_index(drop=True)

    # 3. Calcular el ancho y la posición
    anchos = df_sorted['Potencial'].tolist()
    alturas = df_sorted['Costo'].tolist()
    nombres = df_sorted['Medida'].fillna("Sin Nombre").tolist() # Si no ponen nombre, ponemos uno por defecto
    
    # Calcular coordenadas X
    x_centers = []
    acumulado = 0
    
    for w in anchos:
        # Aquí fallaba antes porque w era None. Ahora w siempre será un número.
        center = acumulado + (w / 2)
        x_centers.append(center)
        acumulado += w

    # Colores
    colores = ['#2ecc71' if x < 0 else '#e74c3c' for x in alturas]

    # --- SECCIÓN 4: VISUALIZACIÓN ---
    fig = go.Figure()
    
    # (El resto del código de la gráfica sigue igual...)
    fig.add_trace(go.Bar(
        x=x_centers,
        y=alturas,
        width=anchos,
        marker_color=colores,
        text=nombres,
        hovertemplate='<b>%{text}</b><br>Costo: $%{y:.2f}<br>Potencial: %{width} t<extra></extra>',
        opacity=0.8,
        marker_line_color='black',
        marker_line_width=1
    ))

    fig.update_layout(
        title="Curva de Costo Marginal de Abatimiento",
        xaxis_title="Potencial de Abatimiento (tCO2e)",
        yaxis_title="Costo Marginal ($/tCO2e)",
        bargap=0,
        template="plotly_white",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- SECCIÓN 5: EXPORTAR ---
    csv = df_sorted.to_csv(index=False).encode('utf-8')
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Descargar Datos (CSV)",
            data=csv,
            file_name="datos_macc.csv",
            mime="text/csv",
        )
    with col2:
        st.caption("📷 Para descargar imagen: usa la cámara en la esquina del gráfico.")

else:
    # Mensaje bonito si borran todos los datos
    st.info("👋 Agrega datos a la tabla para ver el gráfico.")