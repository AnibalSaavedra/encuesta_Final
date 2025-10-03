import os
import streamlit as st
import pandas as pd
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from PIL import Image
from datetime import datetime
from io import StringIO

# ---------- Credenciales ----------
load_dotenv(override=True)
SMTP_USER = os.getenv("SMTP_USER") or st.secrets.get("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS") or st.secrets.get("SMTP_PASS")
REPORTE_TO = os.getenv("REPORTE_TO") or st.secrets.get("REPORTE_TO") or "estudios.preventivos@gmail.com"
if SMTP_PASS:
    SMTP_PASS = SMTP_PASS.replace(" ", "")  # limpia espacios

# ---------- Página ----------
st.set_page_config(page_title="Encuesta de Satisfacción – CRB", page_icon="🧪", layout="centered")

# Logo robusto
def mostrar_logo(path):
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            st.image(Image.open(path), width=180)
    except Exception:
        pass
mostrar_logo("logo_crb.png")

st.markdown("## Encuesta de Satisfacción – Toma de Muestras")
st.caption("Tu opinión es muy importante para mejorar nuestro servicio.")

# ---------- Consentimiento ----------
if "consent" not in st.session_state:
    st.session_state["consent"] = False

if not st.session_state["consent"]:
    st.markdown(
        """
        ### Consentimiento informado
        - Esta encuesta **no solicita** ni almacena datos personales sensibles.
        - Puedes **responder de forma anónima**.
        - Usaremos tus respuestas solo con fines de **mejora de la calidad** del servicio.
        - Al continuar, aceptas nuestros **términos, condiciones y consentimiento** para el uso de tu información **ad hoc**.
        """
    )
    acepto = st.checkbox("He leído y **acepto** los términos, condiciones y consentimiento.")
    if st.button("Acepto y continuar", type="primary", disabled=not acepto):
        st.session_state["consent"] = True
        # FIX: Streamlit 1.32+ usa st.rerun() (experimental_rerun ya no existe)
        st.rerun()
    st.stop()

# ---------- Formulario ----------
with st.form("form_encuesta", clear_on_submit=True):
    anonimo = st.checkbox("Quiero responder de forma **anónima**")
    nombre = st.text_input("Identificación (opcional)", disabled=anonimo, placeholder="Tu nombre o identificación")
    correo = st.text_input("Correo (para retroalimentación, opcional)")
    st.divider()

    p1 = st.text_area(
        "1) ¿Qué espera usted de una atención en toma de muestras?",
        max_chars=220, height=100,
        placeholder="Escribe tu respuesta (máx. 220 caracteres)"
    )
    p2 = st.selectbox(
        "2) ¿Su atención cumplió con sus expectativas (lo que esperaba)?",
        ["", "Sí", "No", "Parcial"], index=0
    )
    p3 = st.text_area(
        "3) ¿Cómo podríamos contribuir a mejorar tu experiencia?",
        max_chars=220, height=100,
        placeholder="Cuéntanos cómo mejorar (máx. 220 caracteres)"
    )

    enviado = st.form_submit_button("Enviar respuesta", type="primary")

# ---------- Utilidad de correo ----------
def enviar_correo_con_adjunto_csv(recip, subject, body, df_adj, filename="respuesta_encuesta.csv"):
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(SMTP_USER, SMTP_PASS)
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = recip
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Crear CSV en memoria y adjuntar
        csv_buffer = StringIO()
        df_adj.to_csv(csv_buffer, index=False, encoding="utf-8")
        csv_bytes = csv_buffer.getvalue().encode("utf-8")

        part = MIMEBase("application", "octet-stream")
        part.set_payload(csv_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

        server.sendmail(SMTP_USER, recip, msg.as_string())

def enviar_correo_simple(recip, subject, body):
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(SMTP_USER, SMTP_PASS)
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = recip
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        server.sendmail(SMTP_USER, recip, msg.as_string())

# ---------- Envío ----------
if enviado:
    if not any([(p1 or '').strip(), (p2 or '').strip(), (p3 or '').strip()]):
        st.error("Por favor responde al menos una de las preguntas antes de enviar.")
        st.stop()

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datos = {
        "timestamp": ts,
        "anonimo": "Sí" if anonimo else "No",
        "identificacion": "" if anonimo else (nombre or "").strip(),
        "correo_usuario": (correo or "").strip(),
        "p1_espera_atencion": (p1 or "").strip(),
        "p2_cumplio_expectativas": (p2 or "").strip(),
        "p3_mejoras": (p3 or "").strip(),
    }
    df = pd.DataFrame([datos])

    # Guardar CSV (append)
    if os.path.exists("respuestas_encuesta.csv"):
        df.to_csv("respuestas_encuesta.csv", mode="a", header=False, index=False, encoding="utf-8")
    else:
        df.to_csv("respuestas_encuesta.csv", index=False, encoding="utf-8")

    if not (SMTP_USER and SMTP_PASS and REPORTE_TO):
        faltan = [k for k,v in {"SMTP_USER":SMTP_USER,"SMTP_PASS":SMTP_PASS,"REPORTE_TO":REPORTE_TO}.items() if not v]
        st.warning("⚠️ Respuesta guardada pero no se pudo enviar el correo. Faltan: " + ", ".join(faltan))
    else:
        try:
            # --- Reporte con adjunto CSV ---
            body_rep = f"""📩 Nuevo reporte de Encuesta CRB

Fecha/Hora: {ts}
Anónimo: {datos['anonimo']}
Identificación: {datos['identificacion']}
Correo usuario: {datos['correo_usuario']}

1) ¿Qué espera usted de una atención en toma de muestras?
{datos['p1_espera_atencion']}

2) ¿Su atención cumplió con sus expectativas (lo que esperaba)?
{datos['p2_cumplio_expectativas']}

3) ¿Cómo podríamos contribuir a mejorar tu experiencia?
{datos['p3_mejoras']}
"""
            enviar_correo_con_adjunto_csv(
                REPORTE_TO,
                "Nuevo reporte – Encuesta de Satisfacción CRB",
                body_rep,
                df,
                filename=f"respuesta_encuesta_{ts.replace(':','-').replace(' ','_')}.csv"
            )

            # --- Confirmación al usuario (sin adjunto) ---
            if datos["correo_usuario"]:
                body_usr = f"""Hola {datos['identificacion'] or '👤'},
Gracias por responder la Encuesta de Satisfacción – CRB.

Copia de tus respuestas:
1) {datos['p1_espera_atencion'] or '-'}
2) {datos['p2_cumplio_expectativas'] or '-'}
3) {datos['p3_mejoras'] or '-'}

Atte., Equipo CRB"""
                enviar_correo_simple(datos["correo_usuario"], "Confirmación – Encuesta de Satisfacción CRB", body_usr)

            st.success("✅ ¡Gracias! Respuesta enviada. (Se guardó y se envió el reporte con adjunto CSV.)")
        except Exception as e:
            st.warning(f"⚠️ Respuesta guardada pero hubo un problema enviando el correo: {e}")
