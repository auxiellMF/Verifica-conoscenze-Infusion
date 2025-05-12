import streamlit as st  
import pandas as pd
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime
import os

st.set_page_config(page_title="Quiz auxiell", layout="centered")

# Logo fisso
st.markdown("""
    <style>
    .fixed-logo-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #000 !important;
        text-align: center;
        padding-top: 65px;
        padding-bottom: 0px;
        z-index: 1000;
        box-shadow: 0px 2px 4px rgba(255,255,255,0.1);
    }
    .fixed-logo-container img {
        max-height: 80px;
    }
    .fixed-logo-divider {
        border: none;
        height: 1px;
        background-color: #ccc;
        margin: 0;
        padding: 0;
    }
    .spacer { height: 140px; }
    </style>
    <div class="fixed-logo-container">
        <img src="https://raw.githubusercontent.com/auxiellMF/prova/0e7fd16a41139ea306af35cc0f6dccb852403b86/auxiell_logobase.png" alt="Logo Auxiell">
        <hr class="fixed-logo-divider">
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

st.title("Verifica competenze Infusion")

# Stato iniziale
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "proseguito" not in st.session_state:
    st.session_state["proseguito"] = False
if "azienda_scelta" not in st.session_state:
    st.session_state["azienda_scelta"] = None
if "questionario_scelto" not in st.session_state:
    st.session_state["questionario_scelto"] = None
if "email_inviata" not in st.session_state:
    st.session_state["email_inviata"] = False

# Step 1: selezione azienda
if st.session_state["azienda_scelta"] is None:
    aziende_disponibili = ["auxiell", "euxilia", "xva"]
    azienda_scelta = st.selectbox("Seleziona la tua azienda", aziende_disponibili)
    if st.button("Conferma azienda"):
        st.session_state["azienda_scelta"] = azienda_scelta
    st.stop()

# Step 2: selezione questionario
if st.session_state["questionario_scelto"] is None:
    questionari = [
        "test video new entry",
        "test conoscenze infusion",
        "test corso feedback",
        "test bibliografia essenziale",
        "test cybersecurity",
        "test conoscenze generiche materiale infusion",
        "test best practice per andare da cliente",
        "test bignami"
    ]
    questionario_scelto = st.selectbox("Quale questionario vuoi fare?", questionari)
    if st.button("Conferma questionario"):
        st.session_state["questionario_scelto"] = questionario_scelto
    st.stop()

# Caricamento Excel in base al questionario scelto
file_path = f"{st.session_state['questionario_scelto']}.xlsx"
if not os.path.exists(file_path):
    st.error(f"File non trovato: {file_path}")
    st.stop()
try:
    df = pd.read_excel(file_path)
    st.success("Domande pronte!")
except Exception as e:
    st.error(f"Errore nel caricamento del file: {e}")
    st.stop()

# Step 3: input utente
utente = st.text_input("Inserisci il tuo nome")
email_compilatore = st.text_input("Inserisci la tua email aziendale")
email_mentor = st.text_input("Inserisci l'indirizzo e-mail del tuo main mentor")

# Validazione email
errore_email = None
dominio_atteso = {
    "auxiell": "@auxiell.com",
    "euxilia": "@euxilia.com",
    "xva": "@xva-services.com"
}
dominio = dominio_atteso.get(st.session_state["azienda_scelta"].lower(), "@auxiell.com")

if email_compilatore and not email_compilatore.endswith(dominio):
    errore_email = f"La tua email deve terminare con {dominio}"
elif email_mentor and not email_mentor.endswith(dominio):
    errore_email = f"L'email del mentor deve terminare con {dominio}"
elif email_compilatore and email_mentor and email_compilatore == email_mentor:
    errore_email = "La tua email e quella del mentor devono essere diverse"

if errore_email:
    st.warning(errore_email)

if utente and email_compilatore and email_mentor and not errore_email and not st.session_state["proseguito"]:
    st.markdown("<div style='text-align: center; margin-top:20px;'><br>", unsafe_allow_html=True)
    if st.button("Prosegui"):
        st.session_state["proseguito"] = True
    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state["proseguito"]:
    risposte = []
    st.write("### Rispondi alle seguenti domande:")

    option_cols = [c for c in df.columns if c.lower().strip().startswith("opzione")]

    for idx, row in df.iterrows():
        st.markdown(f"**{row['Domanda']}**")
        if pd.isna(row.get("opzione 1")):
            ans = st.text_input(f"Risposta libera ({row['principio']})", key=f"open_{idx}", disabled=st.session_state["submitted"])
            risposte.append({
                "Tipo": "aperta",
                "Azienda": st.session_state["azienda_scelta"],
                "Utente": utente,
                "Domanda": row["Domanda"],
                "Argomento": row["principio"],
                "Risposta": ans,
                "Corretta": None,
                "Esatta": None
            })
        else:
            opts = [str(row[c]) for c in option_cols if pd.notna(row[c])]
            corrette = [c.strip() for c in str(row["Corretta"]).split(";")]

            if len(corrette) > 1:
                sel = st.multiselect(f"(Risposte multiple) Argomento: {row['principio']}", opts, key=idx, default=[], disabled=st.session_state["submitted"])
                is_corr = set(sel) == set(corrette)
            else:
                sel = st.radio(f"Argomento: {row['principio']}", opts, key=idx, index=None, disabled=st.session_state["submitted"])
                is_corr = sel == corrette[0]

            risposte.append({
                "Tipo": "chiusa",
                "Azienda": st.session_state["azienda_scelta"],
                "Utente": utente,
                "Domanda": row["Domanda"],
                "Argomento": row["principio"],
                "Risposta": "; ".join(sel) if isinstance(sel, list) else sel,
                "Corretta": row["Corretta"],
                "Esatta": is_corr
            })

    if not st.session_state["submitted"]:
        if st.button("Invia Risposte"):
            st.session_state["submitted"] = True
            st.rerun()

if st.session_state["submitted"]:
    st.success("Risposte inviate.")
    df_r = pd.DataFrame(risposte)
    chiuse = df_r[df_r["Tipo"] == "chiusa"]
    n_tot = len(chiuse)
    n_cor = int(chiuse["Esatta"].sum()) if n_tot else 0
    perc = int(n_cor / n_tot * 100) if n_tot else 0
    st.success(f"Punteggio finale: {n_cor} su {n_tot} ({perc}%)")

    data_test = datetime.now().strftime("%d/%m/%Y")
    info = pd.DataFrame([{ "Nome": utente, "Data": data_test, "Punteggio": f"{perc}%", "Azienda": st.session_state["azienda_scelta"] }])
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        info.to_excel(writer, index=False, sheet_name="Risposte", startrow=0)
        pd.DataFrame([], columns=[""]).to_excel(writer, index=False, sheet_name="Risposte", startrow=2)
        df_r["Email"] = email_compilatore
        df_r["Punteggio"] = f"{perc}%"
        df_r.to_excel(writer, index=False, sheet_name="Risposte", startrow=3)
    buf.seek(0)

    if not st.session_state["email_inviata"]:
        msg = MIMEMultipart()
        msg["From"] = "infusionauxiell@gmail.com"
        msg["To"] = email_mentor
        msg["Subject"] = f"Risultati Quiz - {utente}"
        body = f"Risultati di {utente} ({email_compilatore}) in allegato.\nPunteggio: {perc}%"
        msg.attach(MIMEText(body, "plain"))
        attachment = MIMEApplication(buf.getvalue(), Name=f"risultati_{utente}.xlsx")
        attachment["Content-Disposition"] = f'attachment; filename="risultati_{utente}.xlsx"'
        msg.attach(attachment)

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login("infusionauxiell@gmail.com", "TUA_PASSWORD_PER_APP")
                server.send_message(msg)
            st.success(f"Email inviata a {email_mentor}")
            st.session_state["email_inviata"] = True
        except Exception as e:
            st.error(f"Errore durante l'invio email: {e}")
