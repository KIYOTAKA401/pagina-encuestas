import streamlit as st
from supabase import create_client
from datetime import datetime
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np

# --- Configuración de Supabase ---
SUPABASE_URL = "https://socgmmemdzxxuhmmlalp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNvY2dtbWVtZHp4eHVobW1sYWxwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQxNjYzMzUsImV4cCI6MjA1OTc0MjMzNX0.Qp10puEQ7_DY195lzNvbOpjvjkpcwCmsSnfzafvdleU"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Configuración de la App ---
st.set_page_config(page_title="Escáner QR Asistencia", layout="centered")
st.title("📷 Escanear QR para Registrar Asistencia")

# --- Captura desde cámara ---
image = st.camera_input("Escanea tu código QR")

if image:
    img = Image.open(image)
    img_np = np.array(img)
    decoded = decode(img_np)

    if decoded:
        data = decoded[0].data.decode("utf-8")
        st.success(f"QR detectado: {data}")

        # Guardar en Supabase
        try:
            now = datetime.now()
            supabase.table("asistencias").insert({
                "nombre": data,
                "materia": "General",
                "id_materia": "QR1",
                "fecha": now.strftime("%Y-%m-%d"),
                "hora": now.strftime("%H:%M:%S")
            }).execute()
            st.success("✅ Asistencia registrada correctamente.")
        except Exception as e:
            st.error(f"❌ Error al guardar en Supabase: {e}")
    else:
        st.warning("⚠️ No se detectó ningún código QR.")