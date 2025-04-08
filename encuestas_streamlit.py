from pathlib import Path
import json

RUTA_USUARIOS = Path("usuarios.json")

def cargar_usuarios():
    if RUTA_USUARIOS.exists():
        with open(RUTA_USUARIOS, "r") as f:
            return json.load(f)
    return {}

def guardar_usuarios(usuarios):
    with open(RUTA_USUARIOS, "w") as f:
        json.dump(usuarios, f, indent=4)

usuarios = cargar_usuarios()

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configuración inicial de la página
st.set_page_config(page_title="Portal de Encuestas", page_icon="📊", layout="wide")

# Diccionarios en sesión
if 'usuarios' not in st.session_state:
    st.session_state.usuarios = {}  # {usuario: {"nombre": ..., "apellido": ..., "correo": ..., "contraseña": ...}}
if 'usuario_autenticado' not in st.session_state:
    st.session_state.usuario_autenticado = None
if 'encuestas' not in st.session_state:
    st.session_state.encuestas = {}

# Página de registro
def registrar_usuario():
    st.title("📝 Registro de Usuario")
    with st.form("form_registro"):
        usuario = st.text_input("Nombre de usuario")
        nombre = st.text_input("Nombre")
        apellido = st.text_input("Apellido")
        correo = st.text_input("Correo electrónico")
        contraseña = st.text_input("Contraseña", type="password")
        confirmar = st.text_input("Confirmar contraseña", type="password")
        submit = st.form_submit_button("Registrar")

        if submit:
            if not usuario or not nombre or not apellido or not correo or not contraseña:
                st.error("Todos los campos son obligatorios.")
            elif contraseña != confirmar:
                st.error("Las contraseñas no coinciden.")
            elif usuario in st.session_state.usuarios:
                st.error("El nombre de usuario ya existe.")
            else:
                st.session_state.usuarios[usuario] = {
                    "nombre": nombre,
                    "apellido": apellido,
                    "correo": correo,
                    "contraseña": contraseña
                }
                st.success("Usuario registrado correctamente. Ahora puedes iniciar sesión.")

# Página de inicio de sesión
def iniciar_sesion():
    st.title("🔐 Iniciar Sesión")
    with st.form("form_login"):
        usuario = st.text_input("Usuario")
        contraseña = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")

        if submit:
            usuario_data = st.session_state.usuarios.get(usuario)
            if usuario_data and usuario_data["contraseña"] == contraseña:
                st.session_state.usuario_autenticado = usuario
                st.success(f"Bienvenido {usuario_data['nombre']} 👋")
            else:
                st.error("Usuario o contraseña incorrectos.")

# Función para cerrar sesión
def cerrar_sesion():
    st.session_state.usuario_autenticado = None
    st.success("Sesión cerrada correctamente.")

# Función para crear una nueva encuesta
def crear_encuesta():
    st.subheader("Crear Nueva Encuesta")
    with st.form("form_crear_encuesta"):
        titulo = st.text_input("Título de la encuesta")
        descripcion = st.text_area("Descripción")
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
            if tipo_pregunta == "Selección múltiple":
                opciones = st.text_input(f"Opciones (separadas por comas) para pregunta {i+1}", help="Ejemplo: Opción 1, Opción 2, Opción 3")
                opciones = [op.strip() for op in opciones.split(",") if op.strip()]
            else:
                opciones = []
            preguntas.append({"texto": texto_pregunta, "tipo": tipo_pregunta, "opciones": opciones})
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
    encuesta_seleccionada = st.selectbox("Selecciona una encuesta para responder", list(st.session_state.encuestas.keys()))
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
    encuesta_seleccionada = st.selectbox("Selecciona una encuesta para analizar", list(st.session_state.encuestas.keys()))
    encuesta = st.session_state.encuestas[encuesta_seleccionada]
    st.markdown(f"## Análisis de: {encuesta_seleccionada}")
    st.write(f"**Descripción:** {encuesta['descripcion']}")
    st.write(f"**Total de respuestas:** {len(encuesta['respuestas'])}")
    if not encuesta["respuestas"]:
        st.warning("Esta encuesta no tiene respuestas aún.")
        return
    for i, pregunta in enumerate(encuesta["preguntas"]):
        st.markdown(f"### Pregunta {i+1}: {pregunta['texto']}")
        respuestas_pregunta = [respuesta[i] for respuesta in encuesta["respuestas"]]
        if pregunta["tipo"] == "Texto abierto":
            st.write("**Respuestas textuales:**")
            for j, respuesta in enumerate(respuestas_pregunta, 1):
                st.write(f"{j}. {respuesta}")
        elif pregunta["tipo"] in ["Selección múltiple", "Escala (1-5)"]:
            df = pd.DataFrame({"respuesta": respuestas_pregunta})
            st.write("**Estadísticas:**")
            st.write(df["respuesta"].describe())
            st.write("**Distribución de respuestas:**")
            fig, ax = plt.subplots()
            if pregunta["tipo"] == "Escala (1-5)":
                sns.histplot(data=df, x="respuesta", bins=5, discrete=True, ax=ax)
                ax.set_xticks(range(1, 6))
            else:
                sns.countplot(data=df, y="respuesta", ax=ax, order=df["respuesta"].value_counts().index)
            st.pyplot(fig)
            st.write("**Frecuencia de respuestas:**")
            freq_table = df["respuesta"].value_counts().reset_index()
            freq_table.columns = ["Respuesta", "Frecuencia"]
            st.dataframe(freq_table)

# Menú principal del portal (solo si está autenticado)
def portal_encuestas():
    st.sidebar.title("Menú")
    opcion = st.sidebar.radio("Selecciona una opción:", 
                              ["Inicio", "Crear Encuesta", "Responder Encuesta", "Analizar Encuesta", "Cerrar Sesión"])
    if opcion == "Inicio":
        st.write("## Bienvenido al Portal de Encuestas y Análisis de Datos")
        st.write("Esta plataforma te permite: "
        "- Crear encuestas personalizadas"
        "- Recolectar respuestas"
        "- Visualizar resultados con análisis estadístico"
        "- Generar gráficos interactivos")
    elif opcion == "Crear Encuesta":
        crear_encuesta()
    elif opcion == "Responder Encuesta":
        responder_encuesta()
    elif opcion == "Analizar Encuesta":
        analizar_encuesta()
    elif opcion == "Cerrar Sesión":
        cerrar_sesion()

# Punto de entrada
def main():
    if st.session_state.usuario_autenticado:
        portal_encuestas()
    else:
        st.sidebar.title("Acceso")
        opcion = st.sidebar.radio("Selecciona una opción:", ["Iniciar Sesión", "Registrarse"])
        if opcion == "Iniciar Sesión":
            iniciar_sesion()
        else:
            registrar_usuario()

if __name__ == "__main__":
    main()
