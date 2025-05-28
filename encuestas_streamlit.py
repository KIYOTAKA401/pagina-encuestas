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
if "encuesta_respondida" not in st.session_state:
    st.session_state.encuesta_respondida = False

# ----------------- FUNCIONES AUXILIARES -----------------

def generar_qr(link):
    qr = qrcode.make(link)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return buf

def verificar_conexion():
    try:
        # Verifica conexión y permisos
        res = supabase.table("encuestas").select("id").limit(1).execute()
        return True
    except Exception as e:
        st.error(f"Error de conexión con Supabase: {str(e)}")
        st.error("Verifica que:")
        st.error("- La URL y KEY de Supabase son correctos")
        st.error("- La tabla 'encuestas' existe en tu base de datos")
        st.error("- Tienes permisos de escritura")
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
    st.session_state.encuesta_respondida = False
    st.success("Sesión cerrada correctamente.")

# ----------------- FUNCIONES DE ENCUESTA -----------------
def actualizar_num_preguntas():
    st.session_state.num_preguntas_guardado = st.session_state.num_preguntas

def crear_encuesta():
    st.title("📋 Crear Encuesta")

    # Estados iniciales
    if "num_preguntas" not in st.session_state:
        st.session_state.num_preguntas = 1
    if "textos_preguntas" not in st.session_state:
        st.session_state.textos_preguntas = [""] * 10
    if "tipos_preguntas" not in st.session_state:
        st.session_state.tipos_preguntas = ["Texto"] * 10
    if "opciones_preguntas" not in st.session_state:
        st.session_state.opciones_preguntas = [""] * 10

    # Configurador fuera del formulario
    st.session_state.num_preguntas = st.slider(
        "Selecciona el número de preguntas",
        min_value=1,
        max_value=10,
        value=st.session_state.num_preguntas
    )

tipos_disponibles = ["Texto", "Opción múltiple", "Escala (1-5)"]

for i in range(st.session_state.num_preguntas):
    st.markdown(f"---\n### Pregunta {i+1}")
    col1, col2 = st.columns([5, 1])
    
    with col1:
        st.session_state.textos_preguntas[i] = st.text_input(
            f"Texto de la pregunta {i+1}",
            value=st.session_state.textos_preguntas[i],
            key=f"texto_{i}"
        )
        st.write(f"Tipo de pregunta: {st.session_state.tipos_preguntas[i]}")
        
        # Mostrar opciones si es opción múltiple
        if st.session_state.tipos_preguntas[i] == "Opción múltiple":
            st.session_state.opciones_preguntas[i] = st.text_input(
                f"Opciones separadas por coma para pregunta {i+1}",
                value=st.session_state.opciones_preguntas[i],
                key=f"opciones_{i}",
                help="Ejemplo: Opción 1, Opción 2"
            )

    with col2:
        if st.button(f"Cambiar tipo {i}", key=f"cambiar_tipo_{i}"):
            tipo_actual = st.session_state.tipos_preguntas[i]
            nuevo_tipo = tipos_disponibles[(tipos_disponibles.index(tipo_actual) + 1) % len(tipos_disponibles)]
            st.session_state.tipos_preguntas[i] = nuevo_tipo
            st.experimental_rerun()  # Para refrescar la interfaz y que el cambio se note

        try:
            encuesta_id = str(uuid.uuid4())
            # Simulación: Aquí deberías usar supabase
            st.success("Encuesta creada con éxito")
            enlace = f"https://pagina-encuestas.streamlit.app/?id={encuesta_id}"
            st.markdown(f"**Enlace para responder:** [{enlace}]({enlace})")
        except Exception as e:
            st.error(f"Error al crear la encuesta: {str(e)}")
            
def mostrar_resultados(encuesta_id):
    try:
        # Obtener la encuesta
        res_encuesta = supabase.table("encuestas").select("*").eq("id", encuesta_id).execute()
        if not res_encuesta.data:
            st.error("Encuesta no encontrada.")
            return
        
        encuesta = res_encuesta.data[0]
        preguntas = json.loads(encuesta["preguntas"])
        
        # Obtener todas las respuestas
        res_respuestas = supabase.table("respuestas").select("*").eq("encuesta_id", encuesta_id).execute()
        if not res_respuestas.data:
            st.warning("Aún no hay respuestas para esta encuesta.")
            return
            
        respuestas = [json.loads(r["respuestas"]) for r in res_respuestas.data]
        
        st.title(f"📊 Resultados: {encuesta['titulo']}")
        st.write(encuesta['descripcion'])
        st.markdown(f"**Total de respuestas:** {len(respuestas)}")
        
        for i, pregunta in enumerate(preguntas):
            st.markdown(f"### {pregunta['texto']}")
            
            if pregunta["tipo"] == "Texto":
                # Mostrar respuestas textuales
                respuestas_pregunta = [r[pregunta["texto"]] for r in respuestas]
                st.write(pd.DataFrame(respuestas_pregunta, columns=["Respuestas"]))
                
            elif pregunta["tipo"] == "Opción múltiple":
                # Gráfico de barras para opciones
                respuestas_pregunta = [r[pregunta["texto"]] for r in respuestas]
                counts = pd.Series(respuestas_pregunta).value_counts()
                
                fig, ax = plt.subplots()
                counts.plot(kind='bar', ax=ax)
                ax.set_title(f"Respuestas: {pregunta['texto']}")
                ax.set_ylabel("Cantidad")
                st.pyplot(fig)
                
                # Mostrar tabla con porcentajes
                df = pd.DataFrame({
                    "Opción": counts.index,
                    "Votos": counts.values,
                    "%": (counts.values / counts.sum() * 100).round(1)
                })
                st.dataframe(df)
                
            elif pregunta["tipo"] == "Escala (1-5)":
                # Histograma para escala
                respuestas_pregunta = [int(r[pregunta["texto"]]) for r in respuestas]
                
                fig, ax = plt.subplots()
                sns.histplot(respuestas_pregunta, bins=5, discrete=True, ax=ax)
                ax.set_title(f"Distribución de respuestas (1-5)")
                ax.set_xlabel("Valor")
                ax.set_ylabel("Cantidad")
                st.pyplot(fig)
                
                # Estadísticas
                st.write(f"Promedio: {pd.Series(respuestas_pregunta).mean():.2f}")
                st.write(f"Moda: {pd.Series(respuestas_pregunta).mode()[0]}")
                
    except Exception as e:
        st.error(f"Error al mostrar resultados: {str(e)}")

def mostrar_encuesta_publica(encuesta_id):
    try:
        query_params = st.query_params
        ver_resultados = query_params.get("resultados", None)   
        
        if ver_resultados:
            mostrar_resultados(encuesta_id)
            return
            
        if st.session_state.encuesta_respondida:
            mostrar_resultados(encuesta_id)
            return

        res = supabase.table("encuestas").select("*").eq("id", encuesta_id).execute()
        if not res.data:
            st.error("Encuesta no encontrada.")
            return

        encuesta = res.data[0]
        st.title(f"📊 {encuesta['titulo']}")
        st.write(encuesta['descripcion'])
        preguntas = json.loads(encuesta["preguntas"])
        respuestas = {}

        with st.form("form_responder_encuesta"):
            for i, pregunta in enumerate(preguntas):
                st.markdown(f"**{pregunta['texto']}**")
                if pregunta["tipo"] == "Texto":
                    respuesta = st.text_input("Tu respuesta:", key=f"respuesta_{i}")
                elif pregunta["tipo"] == "Opción múltiple":
                    respuesta = st.radio("Selecciona una opción:", pregunta["opciones"], key=f"respuesta_{i}")
                elif pregunta["tipo"] == "Escala (1-5)":
                    respuesta = st.slider("Selecciona un valor:", 1, 5, key=f"respuesta_{i}")
                else:
                    respuesta = ""
                respuestas[pregunta["texto"]] = respuesta

            if st.form_submit_button("Enviar respuestas"):
                supabase.table("respuestas").insert({
                    "encuesta_id": encuesta_id,
                    "respuestas": json.dumps(respuestas)
                }).execute()
                st.session_state.encuesta_respondida = True
                st.success("✅ ¡Gracias por responder la encuesta!")
                st.markdown("### Resultados de la encuesta")
                mostrar_resultados(encuesta_id)

    except Exception as e:
        st.error(f"Error al mostrar la encuesta: {str(e)}")

def mis_encuestas():
    st.title("📋 Mis Encuestas")
    try:
        res = supabase.table("encuestas").select("*").eq("creador", st.session_state.usuario_autenticado).execute()
        
        if not res.data:
            st.info("Aún no has creado ninguna encuesta.")
            return
            
        for encuesta in res.data:
            with st.expander(f"{encuesta['titulo']} - {len(encuesta.get('respuestas', []))} respuestas"):
                st.write(encuesta['descripcion'])
                enlace = f"https://pagina-encuestas-zvfefqjjv3cagabjpvwexj.streamlit.app/?id={encuesta['id']}"
                enlace_resultados = f"{enlace}&resultados=1"
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("[Enlace para responder](" + enlace + ")")
                with col2:
                    st.markdown("[Enlace para ver resultados](" + enlace_resultados + ")")
                
                if st.button(f"Ver resultados completos", key=f"resultados_{encuesta['id']}"):
                    mostrar_resultados(encuesta['id'])

    except Exception as e:
        st.error(f"Error al obtener encuestas: {str(e)}")

def main():
    if not verificar_conexion():
        return

    query_params = st.query_params
    encuesta_id = query_params.get("id", None)

    if encuesta_id:
        mostrar_encuesta_publica(encuesta_id)
        return

    if st.session_state.usuario_autenticado:
        st.sidebar.title("Menú")
        opcion = st.sidebar.radio("Selecciona una opción", 
                                ["Inicio", "Crear Encuesta", "Mis Encuestas", "Cerrar Sesión"])
        
        if opcion == "Inicio":
            st.write("Bienvenido al portal de encuestas")
        elif opcion == "Crear Encuesta":
            crear_encuesta()
        elif opcion == "Mis Encuestas":
            mis_encuestas()
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
