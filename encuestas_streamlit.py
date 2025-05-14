import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import bcrypt
import qrcode
import uuid
from io import BytesIO
from supabase import create_client

# Configuración de Supabase
SUPABASE_URL = "https://socgmmemdzxxuhmmlalp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Usa tu clave completa aquí
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración de la página
st.set_page_config(page_title="Portal de Encuestas", page_icon="📊", layout="wide")

# Estado de la sesión
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None
if "encuestas" not in st.session_state:
    st.session_state.encuestas = {}

# ---------------- FUNCIONES AUXILIARES ----------------

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
                res = supabase.rpc('check_user_exists', {'p_usuario': usuario}).execute()
                if res.data and res.data[0]['exists']:
                    st.error("El nombre de usuario ya existe.")
                    return

                res_correo = supabase.rpc('check_email_exists', {'p_correo': correo}).execute()
                if res_correo.data and res_correo.data[0]['exists']:
                    st.error("El correo electrónico ya está registrado.")
                    return

                hash_contrasena = bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

                supabase.rpc('register_user', {
                    'p_usuario': usuario,
                    'p_nombre': nombre,
                    'p_apellido': apellido,
                    'p_correo': correo,
                    'p_contrasena': hash_contrasena
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

def guardar_encuesta(titulo, descripcion, preguntas):
    id_encuesta = str(uuid.uuid4())
    encuesta_data = {
        "id": id_encuesta,
        "titulo": titulo,
        "descripcion": descripcion,
        "preguntas": preguntas
    }
    supabase.table("encuestas").insert(encuesta_data).execute()
    return id_encuesta

def generar_qr(url):
    qr = qrcode.make(url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return buffer

# ---------------- FUNCIONES PRINCIPALES ----------------

def crear_encuesta():
    st.subheader("Crear Nueva Encuesta")
    with st.form("form_crear_encuesta"):
        titulo = st.text_input("Título de la encuesta")
        descripcion = st.text_area("Descripción")
        num_preguntas = st.number_input("Número de preguntas", min_value=1, max_value=10, value=3)
        tipos_pregunta = ["Texto abierto", "Selección múltiple", "Escala (1-5)"]
        preguntas = []

        for i in range(num_preguntas):
            st.markdown(f"### Pregunta {i+1}")
            texto = st.text_input(f"Texto de la pregunta {i+1}", key=f"preg_{i}")
            tipo = st.selectbox(f"Tipo de pregunta {i+1}", tipos_pregunta, key=f"tipo_{i}")

            opciones = []
            if tipo == "Selección múltiple":
                opciones_raw = st.text_area(f"Opciones (una por línea) para pregunta {i+1}", key=f"opciones_{i}")
                opciones = [o.strip() for o in opciones_raw.split("\n") if o.strip()]

            preguntas.append({
                "texto": texto,
                "tipo": tipo,
                "opciones": opciones
            })

        submit = st.form_submit_button("Guardar Encuesta")
        if submit:
            if not titulo:
                st.error("El título es obligatorio.")
                return

            id_encuesta = guardar_encuesta(titulo, descripcion, preguntas)
            st.success(f"Encuesta '{titulo}' guardada correctamente.")

            base_url = st.secrets.get("base_url", "https://pagina-encuestas-zvfefqjjv3cagabjpvwexj.streamlit.app/")  # Puedes definirlo en .streamlit/secrets.toml
            url_encuesta = f"{base_url}?encuesta={id_encuesta}"

            qr_buffer = generar_qr(url_encuesta)
            st.image(qr_buffer, caption="Escanea para responder la encuesta", use_column_width=False)
            st.markdown(f"[🔗 Ir a la encuesta]({url_encuesta})")

def portal_encuestas(encuesta_param=None):
    st.sidebar.title("Menú")
    opcion = st.sidebar.radio("Selecciona una opción:", ["Inicio", "Crear Encuesta", "Cerrar Sesión"])

    if opcion == "Inicio":
        st.write("## Bienvenido al Portal de Encuestas 📊")
        if encuesta_param:
            st.success(f"Encuesta cargada desde QR: {encuesta_param}")
        st.write("Crea, responde y analiza encuestas fácilmente.")
    elif opcion == "Crear Encuesta":
        crear_encuesta()
    elif opcion == "Cerrar Sesión":
        cerrar_sesion()

def main():
    encuesta_param = st.query_params.get("encuesta")
    if not verificar_conexion():
        st.stop()

    if st.session_state.usuario_autenticado:
        portal_encuestas(encuesta_param)
    else:
        st.sidebar.title("Acceso")
        opcion = st.sidebar.radio("Selecciona una opción:", ["Iniciar Sesión", "Registrarse"])
        if opcion == "Iniciar Sesión":
            iniciar_sesion()
        else:
            registrar_usuario()

if __name__ == "__main__":
    main()
