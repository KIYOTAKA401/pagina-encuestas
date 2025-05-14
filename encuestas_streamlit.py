import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import bcrypt
from supabase import create_client
from io import BytesIO
import qrcode
import uuid

# Configuración de Supabase
SUPABASE_URL = "https://socgmmemdzxxuhmmlalp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNvY2dtbWVtZHp4eHVobW1sYWxwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNjYzMzUsImV4cCI6MjA1OTc0MjMzNX0.Qp10puEQ7_DY195lzNvbOpjvjkpcwCmsSnfzafvdleU"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Encuestas", layout="wide")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ---------------- FUNCIONES AUXILIARES ----------------

def generar_qr(link):
    qr = qrcode.make(link)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return buf

def guardar_encuesta(titulo, descripcion, preguntas):
    encuesta_id = str(uuid.uuid4())
    data = {
        "id": encuesta_id,
        "titulo": titulo,
        "descripcion": descripcion,
        "preguntas": preguntas
    }
    supabase.table("encuestas").insert(data).execute()
    return encuesta_id

def cargar_encuesta(encuesta_id):
    res = supabase.table("encuestas").select("*").eq("id", encuesta_id).execute()
    if res.data:
        return res.data[0]
    return None

def guardar_respuesta(encuesta_id, respuestas):
    supabase.table("respuestas").insert({
        "encuesta_id": encuesta_id,
        "respuestas": respuestas
    }).execute()

def obtener_respuestas(encuesta_id):
    res = supabase.table("respuestas").select("*").eq("encuesta_id", encuesta_id).execute()
    return res.data if res.data else []

# ---------------- FUNCIONES DE PÁGINA ----------------

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
                opciones = [o.strip() for o in opciones_str.split(",") if o.strip()]
            preguntas.append({"texto": texto, "tipo": tipo, "opciones": opciones})

        submit = st.form_submit_button("Crear encuesta")

        if submit:
            encuesta_id = guardar_encuesta(titulo, descripcion, preguntas)
            st.success("Encuesta creada correctamente.")
            url = f"{st.secrets.get('public_url', 'http://localhost:8501')}?encuesta={encuesta_id}"
            qr = generar_qr(url)
            st.image(qr, caption="Escanea este código QR para responder la encuesta")
            st.write(f"Enlace directo: {url}")

def responder_encuesta(encuesta):
    st.title(f"📨 Responder: {encuesta['titulo']}")
    st.write(encuesta["descripcion"])

    with st.form("form_respuesta"):
        respuestas = []
        for i, p in enumerate(encuesta["preguntas"]):
            st.subheader(f"{i+1}. {p['texto']}")
            if p["tipo"] == "Texto":
                respuesta = st.text_area("Respuesta", key=f"r_texto_{i}")
            elif p["tipo"] == "Opción múltiple":
                respuesta = st.radio("Selecciona una opción", p["opciones"], key=f"r_opcion_{i}")
            else:
                respuesta = st.slider("Selecciona un valor", 1, 5, key=f"r_escala_{i}")
            respuestas.append(respuesta)

        if st.form_submit_button("Enviar"):
            guardar_respuesta(encuesta["id"], respuestas)
            st.success("¡Gracias por tu respuesta!")

def analizar_encuesta(encuesta):
    st.title(f"📊 Análisis: {encuesta['titulo']}")
    respuestas = obtener_respuestas(encuesta["id"])
    if not respuestas:
        st.warning("Aún no hay respuestas.")
        return

    df = pd.DataFrame([r["respuestas"] for r in respuestas])
    for i, p in enumerate(encuesta["preguntas"]):
        st.subheader(f"{i+1}. {p['texto']}")
        if p["tipo"] == "Texto":
            for r in df[i].dropna():
                st.write(f"- {r}")
        else:
            fig, ax = plt.subplots()
            sns.countplot(y=df[i], ax=ax)
            st.pyplot(fig)

# ---------------- MAIN ----------------

def main():
    query = st.query_params
    encuesta_id = query.get("encuesta", [None])[0]

    if encuesta_id:
        encuesta = cargar_encuesta(encuesta_id)
        if encuesta:
            responder_encuesta(encuesta)
        else:
            st.error("Encuesta no encontrada.")
    else:
        st.sidebar.title("Menú")
        opcion = st.sidebar.radio("Ir a", ["Inicio", "Crear Encuesta", "Analizar Encuesta"])
        if opcion == "Inicio":
            st.title("🗳️ Portal de Encuestas")
            st.write("Crea y comparte encuestas con códigos QR.")
        elif opcion == "Crear Encuesta":
            crear_encuesta()
        elif opcion == "Analizar Encuesta":
            todas = supabase.table("encuestas").select("*").execute().data
            if not todas:
                st.warning("No hay encuestas disponibles.")
                return
            seleccion = st.selectbox("Selecciona una encuesta", options=[(e["titulo"], e["id"]) for e in todas], format_func=lambda x: x[0])
            encuesta = cargar_encuesta(seleccion[1])
            if encuesta:
                analizar_encuesta(encuesta)

if __name__ == "__main__":
    main()
