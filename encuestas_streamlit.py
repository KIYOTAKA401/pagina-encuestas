import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configuración inicial de la página
st.set_page_config(page_title="Portal de Encuestas", page_icon="📊", layout="wide")

# Título principal
st.title("📊 Portal de Encuestas y Análisis de Datos")

# Diccionario para almacenar las encuestas
if 'encuestas' not in st.session_state:
    st.session_state.encuestas = {}

# Función para crear una nueva encuesta
def crear_encuesta():
    st.subheader("Crear Nueva Encuesta")
    
    with st.form("form_crear_encuesta"):
        titulo = st.text_input("Título de la encuesta")
        descripcion = st.text_area("Descripción")
        
        # Preguntas
        st.write("Agregar preguntas:")
        num_preguntas = st.number_input("Número de preguntas", min_value=1, max_value=20, value=3)
        
        preguntas = []
        tipos_pregunta = ["Texto abierto", "Selección múltiple", "Escala (1-5)"]
        
        for i in range(num_preguntas):
            st.markdown(f"### Pregunta {i+1}")
            col1, col2 = st.columns(2)
            with col1:
                texto_pregunta = st.text_input(f"Texto pregunta {i+1}", key=f"pregunta_{i}")
            with col2:
                tipo_pregunta = st.selectbox(f"Tipo de pregunta {i+1}", tipos_pregunta, key=f"tipo_{i}")
            
            # Si es selección múltiple, pedir opciones
            if tipo_pregunta == "Selección múltiple":
                opciones = st.text_input(f"Opciones (separadas por comas) para pregunta {i+1}", 
                                       help="Ejemplo: Opción 1, Opción 2, Opción 3")
                opciones = [op.strip() for op in opciones.split(",") if op.strip()]
            else:
                opciones = []
            
            preguntas.append({
                "texto": texto_pregunta,
                "tipo": tipo_pregunta,
                "opciones": opciones
            })
        
        if st.form_submit_button("Guardar Encuesta"):
            if titulo:
                st.session_state.encuestas[titulo] = {
                    "descripcion": descripcion,
                    "preguntas": preguntas,
                    "respuestas": []
                }
                st.success(f"Encuesta '{titulo}' creada con éxito!")
            else:
                st.error("El título es obligatorio")

# Función para responder encuestas
def responder_encuesta():
    st.subheader("Responder Encuesta")
    
    if not st.session_state.encuestas:
        st.warning("No hay encuestas disponibles para responder.")
        return
    
    encuesta_seleccionada = st.selectbox("Selecciona una encuesta para responder", 
                                       list(st.session_state.encuestas.keys()))
    
    encuesta = st.session_state.encuestas[encuesta_seleccionada]
    
    st.markdown(f"### {encuesta_seleccionada}")
    st.write(encuesta["descripcion"])
    
    with st.form("form_responder_encuesta"):
        respuestas = []
        for i, pregunta in enumerate(encuesta["preguntas"]):
            st.markdown(f"**{i+1}. {pregunta['texto']}**")
            
            if pregunta["tipo"] == "Texto abierto":
                respuesta = st.text_area("Tu respuesta", key=f"respuesta_{i}")
            elif pregunta["tipo"] == "Selección múltiple":
                respuesta = st.radio("Selecciona una opción", pregunta["opciones"], key=f"respuesta_{i}")
            elif pregunta["tipo"] == "Escala (1-5)":
                respuesta = st.slider("Selecciona un valor", 1, 5, 3, key=f"respuesta_{i}")
            
            respuestas.append(respuesta)
        
        if st.form_submit_button("Enviar Respuesta"):
            encuesta["respuestas"].append(respuestas)
            st.success("¡Gracias por responder la encuesta!")

# Función para analizar encuestas
def analizar_encuesta():
    st.subheader("Análisis de Encuestas")
    
    if not st.session_state.encuestas:
        st.warning("No hay encuestas disponibles para analizar.")
        return
    
    encuesta_seleccionada = st.selectbox("Selecciona una encuesta para analizar", 
                                       list(st.session_state.encuestas.keys()))
    
    encuesta = st.session_state.encuestas[encuesta_seleccionada]
    
    st.markdown(f"## Análisis de: {encuesta_seleccionada}")
    st.write(f"**Descripción:** {encuesta['descripcion']}")
    st.write(f"**Total de respuestas:** {len(encuesta['respuestas'])}")
    
    if not encuesta["respuestas"]:
        st.warning("Esta encuesta no tiene respuestas aún.")
        return
    
    # Mostrar análisis por pregunta
    for i, pregunta in enumerate(encuesta["preguntas"]):
        st.markdown(f"### Pregunta {i+1}: {pregunta['texto']}")
        
        # Obtener todas las respuestas para esta pregunta
        respuestas_pregunta = [respuesta[i] for respuesta in encuesta["respuestas"]]
        
        if pregunta["tipo"] == "Texto abierto":
            st.write("**Respuestas textuales:**")
            for j, respuesta in enumerate(respuestas_pregunta, 1):
                st.write(f"{j}. {respuesta}")
        
        elif pregunta["tipo"] in ["Selección múltiple", "Escala (1-5)"]:
            # Convertir a DataFrame para análisis
            df = pd.DataFrame({"respuesta": respuestas_pregunta})
            
            # Estadísticas básicas
            st.write("**Estadísticas:**")
            st.write(df["respuesta"].describe())
            
            # Visualización
            st.write("**Distribución de respuestas:**")
            
            fig, ax = plt.subplots()
            if pregunta["tipo"] == "Escala (1-5)":
                sns.histplot(data=df, x="respuesta", bins=5, discrete=True, ax=ax)
                ax.set_xticks(range(1, 6))
            else:
                sns.countplot(data=df, y="respuesta", ax=ax, order=df["respuesta"].value_counts().index)
            
            st.pyplot(fig)
            
            # Mostrar tabla de frecuencias
            st.write("**Frecuencia de respuestas:**")
            freq_table = df["respuesta"].value_counts().reset_index()
            freq_table.columns = ["Respuesta", "Frecuencia"]
            st.dataframe(freq_table)

# Menú principal
def main():
    st.sidebar.title("Menú")
    opcion = st.sidebar.radio("Selecciona una opción:", 
                             ["Inicio", "Crear Encuesta", "Responder Encuesta", "Analizar Encuesta"])
    
    if opcion == "Inicio":
        st.write("""
        ## Bienvenido al Portal de Encuestas y Análisis de Datos
        
        Esta plataforma te permite:
        - Crear encuestas personalizadas
        - Recolectar respuestas
        - Visualizar resultados con análisis estadístico
        - Generar gráficos interactivos
        
        Selecciona una opción del menú lateral para comenzar.
        """)
        
    elif opcion == "Crear Encuesta":
        crear_encuesta()
    elif opcion == "Responder Encuesta":
        responder_encuesta()
    elif opcion == "Analizar Encuesta":
        analizar_encuesta()

if __name__ == "__main__":
    main()