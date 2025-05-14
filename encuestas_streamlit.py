import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import bcrypt
from supabase import create_client
from io import BytesIO
import qrcode
import uuid
import json

# Configuración de Supabase
SUPABASE_URL = "https://socgmmemdzxxuhmmlalp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNvY2dtbWVtZHp4eHVobW1sYWxwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNjYzMzUsImV4cCI6MjA1OTc0MjMzNX0.Qp10puEQ7_DY195lzNvbOpjvjkpcwCmsSnfzafvdleU"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Portal de Encuestas", layout="wide")

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

# ---------------- FUNCIONES AUXILIARES ----------------

def generar_qr(link):
    qr = qrcode.make(link)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return buf

def verificar_conexion():
    try:
        supabase.table("usuarios").select("usuario").limit(1).execute()
        return True
    except Exception as e:
        st.error(f"Error de conexión con Supabase: {str(e)}")
        return False

def registrar_usuario():
    st.title("📝 Registro de Usuario")
    with st.form("form_registro"):
        usuario = st.text_input("Nombre de usuario")
        nombre = st.text_input("Nombre")
        apellido = st.text_input("Apellido")
        correo = st.text_input("Correo electrónico")
        contrasena = st.text_input("Contraseña", type="password")
        confirmar = st.text_input("Confirmar contraseña", type="password")
        submit = st.form_submit_button("Registrar")

        if submit:
            if not all([usuario, nombre, apellido, correo, contrasena]):
                st.error("Todos los campos son obligatorios.")
                return
            if contrasena != confirmar:
                st.error("Las contraseñas no coinciden.")
                return
            try:
                hash_contrasena = bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()
                supabase.table("usuarios").insert({
                    "usuario": usuario,
                    "nombre": nombre,
                    "apellido": apellido,
                    "correo": correo,
                    "contrasena": hash_contrasena
                }).execute()
                st.success("Usuario registrado correctamente. Ahora puedes iniciar sesión.")
            except Exception as e:
                st.error(f"Error al registrar usuario: {str(e)}")

def iniciar_sesion():
    st.title("🔐 Iniciar Sesión")
    with st.form("form_login"):
        usuario = st.text_input("Usuario")
        contrasena = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")

        if submit:
            try:
                res = supabase.table("usuarios").select("*").eq("usuario", usuario).execute()
                if res.data:
                    usuario_data = res.data[0]
                    if bcrypt.checkpw(contrasena.encode(), usuario_data["contrasena"].encode()):
                        st.session_state.usuario_autenticado = usuario
                        st.success(f"Bienvenido {usuario_data['nombre']} 👋")
                    else:
                        st.error("Contraseña incorrecta.")
                else:
                    st.error("Usuario no encontrado.")
            except Exception as e:
                st.error(f"Error al iniciar sesión: {str(e)}")

def cerrar_sesion():
    st.session_state.usuario_autenticado = None
    st.success("Sesión cerrada correctamente.")

# ---------------- FUNCIONES DE ENCUESTA ----------------

def crear_encuesta():
    st.title("📋 Crear Encuesta")
    with st.form("form_crear_encuesta"):
        titulo = st.text_input("Título de la encuesta")
        descripcion = st.text_area("Descripción")
        num_preguntas = st.number_input("Número de preguntas", min_value=1, max_value=10, step=1)
        preguntas = []

        for i in range(int(num_preguntas)):
            texto = st.text_input(f"Pregunta {i+1}", key=f"pregunta_{i}")
            tipo = st.selectbox(f"Tipo de pregunta {i+1}", ["Texto", "Opción múltiple", "Escala (1-5)"], key=f"tipo_{i}")
            opciones = []
            if tipo == "Opción múltiple":
                opciones_str = st.text_input(f"Opciones separadas por coma para pregunta {i+1}", key=f"opciones_{i}")
                opciones = [op.strip() for op in opciones_str.split(",") if op.strip()]
            preguntas.append({"texto": texto, "tipo": tipo, "opciones": opciones})

        if st.form_submit_button("Guardar Encuesta"):
            encuesta_id = str(uuid.uuid4())
            supabase.table("encuestas").insert({
                "id": encuesta_id,
                "titulo": titulo,
                "descripcion": descripcion,
                "preguntas": json.dumps(preguntas)
            }).execute()

            enlace = f"https://pagina-encuestas-zvfefqjjv3cagabjpvwexj.streamlit.app/?id={encuesta_id}"
            st.success("Encuesta creada con éxito")
            st.markdown(f"[Haz clic aquí para acceder a la encuesta]({enlace})")
            st.image(generar_qr(enlace), caption="Escanea para responder")

def mostrar_encuesta_publica(encuesta_id):
    try:
        res = supabase.table("encuestas").select("*").eq("id", encuesta_id).execute()
        if not res.data:
            st.error("Encuesta no encontrada.")
            return

        encuesta = res.data[0]
        st.title(encuesta["titulo"])
        st.write(encuesta["descripcion"])

        preguntas = json.loads(encuesta["preguntas"])
        respuestas = []

        with st.form("form_respuesta"):
            for i, pregunta in enumerate(preguntas):
                if pregunta["tipo"] == "Texto":
                    respuesta = st.text_input(pregunta["texto"], key=f"resp_{i}")
                elif pregunta["tipo"] == "Opción múltiple":
                    respuesta = st.radio(pregunta["texto"], pregunta["opciones"], key=f"resp_{i}")
                elif pregunta["tipo"] == "Escala (1-5)":
                    respuesta = st.slider(pregunta["texto"], 1, 5, key=f"resp_{i}")
                else:
                    respuesta = ""
                respuestas.append({"pregunta": pregunta["texto"], "respuesta": respuesta})

            if st.form_submit_button("Enviar respuestas"):
                supabase.table("respuestas").insert({
                    "encuesta_id": encuesta_id,
                    "respuestas": json.dumps(respuestas)
                }).execute()
                st.success("Gracias por tu participación 🎉")

    except Exception as e:
        st.error(f"Error al cargar la encuesta: {str(e)}")


def main():
    if not verificar_conexion():
        return

    query_params = st.experimental_get_query_params()
    encuesta_id = query_params.get("id", [None])[0]

    if encuesta_id:
        mostrar_encuesta_publica(encuesta_id)
        return

    if st.session_state.usuario_autenticado:
        st.sidebar.title("Menú")
        opcion = st.sidebar.radio("Selecciona una opción", ["Inicio", "Crear Encuesta", "Cerrar Sesión"])
        if opcion == "Inicio":
            st.write("Bienvenido al portal de encuestas")
        elif opcion == "Crear Encuesta":
            crear_encuesta()
        elif opcion == "Cerrar Sesión":
            cerrar_sesion()
    else:
        st.sidebar.title("Acceso")
        opcion = st.sidebar.radio("Selecciona una opción", ["Iniciar Sesión", "Registrarse"])
        if opcion == "Iniciar Sesión":
            iniciar_sesion()
        elif opcion == "Registrarse":
            registrar_usuario()


if __name__ == "__main__":
    main()
