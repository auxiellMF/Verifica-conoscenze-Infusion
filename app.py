import streamlit as st  
import pandas as pd
from io import BytesIO
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from PIL import Image

st.set_page_config(page_title="Quiz auxiell", layout="centered")

# Sticky logo in alto
st.markdown("""
    <style>
    .fixed-logo-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: white;
        text-align: center;
        padding-top: 45px;
        padding-bottom: 0px;
        z-index: 1000;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
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
    .spacer {
        height: 140px;
    }
    </style>
    <div class="fixed-logo-container">
        <img src="https://raw.githubusercontent.com/auxiellMF/prova/0e7fd16a41139ea306af35cc0f6dccb852403b86/auxiell_logobase.png" alt="Logo Auxiell">
        <hr class="fixed-logo-divider">
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

st.title("Verifica conoscenze infusion")

if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "proseguito" not in st.session_state:
    st.session_state["proseguito"] = False

file_path = "questionario conoscenze infusion.xlsx"

try:
    df = pd.read_excel(file_path)
    st.success("Domande pronte!")
except FileNotFoundError:
    st.error(f"File non trovato: {file_path}")
    st.stop()

if "principio" in df.columns and "Domanda" in df.columns and "Corretta" in df.columns:

    if "domande_selezionate" not in st.session_state:
        st.session_state["domande_selezionate"] = (
            df.groupby("principio", group_keys=False)
            .apply(lambda x: x.sample(n=min(2, len(x))))
            .reset_index(drop=True)
        )

    domande_selezionate = st.session_state["domande_selezionate"]

    utente = st.text_input("Inserisci il tuo nome")
    email_compilatore = st.text_input("Inserisci la tua email aziendale")
    email_mentor = st.text_input("Inserisci l'indirizzo e-mail del tuo main mentor")

    errore_email = None

    if email_compilatore and not email_compilatore.endswith("@auxiell.com"):
        errore_email = "La tua email deve terminare con @auxiell.com"
    elif email_mentor and not email_mentor.endswith("@auxiell.com"):
        errore_email = "L'email del mentor deve terminare con @auxiell.com"
    elif email_compilatore and email_mentor and email_compilatore == email_mentor:
        errore_email = "La tua email e quella del mentor devono essere diverse"

    if errore_email:
        st.warning(errore_email)

    if utente and email_compilatore and email_mentor and not errore_email and not st.session_state["proseguito"]:
        st.markdown("<div style='text-align: center;'><br><br>", unsafe_allow_html=True)
        if st.button("Prosegui"):
            st.session_state["proseguito"] = True
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["proseguito"]:
        risposte_date = []
        tutte_risposte_date = True
        num_risposte = 0

        st.write("### Rispondi alle seguenti domande:")

        for idx, row in domande_selezionate.iterrows():
            st.markdown(f"**{row['Domanda']}**")

            opzioni = []
            for col in df.columns:
                if "opzione" in col.lower() and pd.notna(row[col]):
                    opzioni.append(str(row[col]))

            risposta = st.radio(
                f"Argomento: {row['principio']}",
                opzioni,
                key=idx,
                index=None,
                disabled=st.session_state["submitted"]
            )

            if not st.session_state["submitted"] and risposta is None:
                tutte_risposte_date = False
            elif risposta is not None:
                num_risposte += 1

            risposte_date.append({
                "Argomento": row["principio"],
                "Domanda": row["Domanda"],
                "Risposta data": risposta,
                "Corretta": row["Corretta"],
                "Risultato": risposta in [c.strip() for c in str(row["Corretta"]).split(";")] if risposta else False
            })

        if not st.session_state["submitted"]:
            if st.button("Invia Risposte"):
                if not tutte_risposte_date:
                    st.warning("Per favore rispondi a tutte le domande prima di inviare.")
                else:
                    st.session_state["submitted"] = True

        if st.session_state["submitted"]:
            risultati_df = pd.DataFrame(risposte_date)
            punteggio = risultati_df["Esatta"].sum()
            st.success(f"Punteggio finale: {punteggio} su {len(domande_selezionate)}")

            risultati_df["Utente"] = utente
            risultati_df["Email"] = email_compilatore

            output = BytesIO()
            risultati_df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            msg = MIMEMultipart()
            msg['From'] = 'tuoindirizzo@gmail.com'
            msg['To'] = email_mentor
            msg['Subject'] = 'Risultati Quiz Verifica Conoscenze'

            body = f"In allegato trovi i risultati del quiz compilati da {utente} ({email_compilatore}).\n\nCordiali saluti."
            msg.attach(MIMEText(body, 'plain'))

            part = MIMEApplication(output.getvalue(), Name=f"risultati_{utente}.xlsx")
            part['Content-Disposition'] = f'attachment; filename="risultati_{utente}.xlsx"'
            msg.attach(part)

            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login('infusionauxiell@gmail.com', 'ubrwqtcnbyjiqach')
                    server.sendmail(msg['From'], msg['To'], msg.as_string())
                st.success(f"Email inviata con successo a {email_mentor}")
            except Exception as e:
                st.error(f"Errore nell'invio dell'email: {str(e)}")

else:
    st.error("Il file Excel deve contenere le colonne: 'principio', 'Domanda', opzioni e 'Corretta'")
