import streamlit as st  
import pandas as pd
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

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
    .spacer { height: 140px; }
    </style>
    <div class="fixed-logo-container">
        <img src="https://raw.githubusercontent.com/auxiellMF/prova/0e7fd16a41139ea306af35cc0f6dccb852403b86/auxiell_logobase.png" alt="Logo Auxiell">
        <hr class="fixed-logo-divider">
    </div>
    <div class="spacer"></div>
""", unsafe_allow_html=True)

st.title("Verifica conoscenze infusion")

# Inizializza stato
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "proseguito" not in st.session_state:
    st.session_state["proseguito"] = False

# Caricamento file
file_path = "questionario conoscenze infusion"
try:
    df = pd.read_excel(file_path)
    st.success("Domande pronte!")
except FileNotFoundError:
    st.error(f"File non trovato: {file_path}")
    st.stop()

# Trova colonne opzione*
option_cols = [c for c in df.columns if c.lower().strip().startswith("opzione")]
if not option_cols:
    st.error("Nessuna colonna di opzione trovata: assicurati di avere colonne che iniziano con 'opzione'.")
    st.stop()

# Controllo colonne obbligatorie
for col in ("principio", "Domanda", "Corretta", "opzione 1"):
    if col not in df.columns:
        st.error(f"Manca la colonna obbligatoria: '{col}'")
        st.stop()

# Selezione casuale delle domande
if "domande_selezionate" not in st.session_state:
    st.session_state["domande_selezionate"] = (
        df.groupby("principio", group_keys=False)
          .apply(lambda x: x.sample(n=min(2, len(x))))
          .reset_index(drop=True)
    )
domande = st.session_state["domande_selezionate"]

# Input utente e email
utente = st.text_input("Inserisci il tuo nome")
email_compilatore = st.text_input("Inserisci la tua email aziendale")
email_mentor = st.text_input("Inserisci l'indirizzo e-mail del tuo main mentor")

# Validazione email
errore_email = None
if email_compilatore and not email_compilatore.endswith("@auxiell.com"):
    errore_email = "La tua email deve terminare con @auxiell.com"
elif email_mentor and not email_mentor.endswith("@auxiell.com"):
    errore_email = "L'email del mentor deve terminare con @auxiell.com"
elif email_compilatore and email_mentor and email_compilatore == email_mentor:
    errore_email = "La tua email e quella del mentor devono essere diverse"
if errore_email:
    st.warning(errore_email)

# Pulsante “Prosegui”
if utente and email_compilatore and email_mentor and not errore_email and not st.session_state["proseguito"]:
    st.markdown("<div style='text-align: center; margin-top:20px;'><br>", unsafe_allow_html=True)
    if st.button("Prosegui"):
        st.session_state["proseguito"] = True
    st.markdown("</div>", unsafe_allow_html=True)

# Quiz
if st.session_state["proseguito"]:
    risposte = []
    st.write("### Rispondi alle seguenti domande:")

    for idx, row in domande.iterrows():
        st.markdown(f"**{row['Domanda']}**")
        # Domanda aperta se 'opzione 1' è NaN
        if pd.isna(row["opzione 1"]):
            ans = st.text_input(
                f"Risposta libera ({row['principio']})",
                key=f"open_{idx}",
                disabled=st.session_state["submitted"]
            )
            risposte.append({
                "Tipo": "aperta",
                "Argomento": row["principio"],
                "Domanda": row["Domanda"],
                "Risposta": ans,
                "Corretta": None,
                "Esatta": None
            })
        else:
            opts = [str(row[c]) for c in option_cols if pd.notna(row[c])]
            sel = st.radio(
                f"Argomento: {row['principio']}",
                opts,
                key=idx,
                index=None,
                disabled=st.session_state["submitted"]
            )
            corrette = [c.strip() for c in str(row["Corretta"]).split(";")]
            is_corr = sel in corrette
            risposte.append({
                "Tipo": "chiusa",
                "Argomento": row["principio"],
                "Domanda": row["Domanda"],
                "Risposta": sel,
                "Corretta": row["Corretta"],
                "Esatta": is_corr
            })

    # Invio risposte
    if not st.session_state["submitted"]:
        if st.button("Invia Risposte"):
            st.session_state["submitted"] = True

    # Calcolo punteggio e invio email
    if st.session_state["submitted"]:
        df_r = pd.DataFrame(risposte)
        chiuse = df_r[df_r["Tipo"] == "chiusa"]
        n_tot = len(chiuse)
        n_cor = int(chiuse["Esatta"].sum()) if n_tot else 0
        perc = int(n_cor / n_tot * 100) if n_tot else 0
        st.success(f"Punteggio finale: {n_cor} su {n_tot} ({perc}%)")

        # Prepara Excel
        df_r["Utente"] = utente
        df_r["Email"] = email_compilatore
        buf = BytesIO()
        df_r.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)

        # Costruisci email
        msg = MIMEMultipart()
        msg["From"] = "tuoindirizzo@gmail.com"
        msg["To"] = email_mentor
        msg["Subject"] = "Risultati Quiz Verifica Conoscenze"
        msg.attach(MIMEText(f"In allegato i risultati di {utente} ({email_compilatore}).", "plain"))
        attachment = MIMEApplication(buf.getvalue(), Name=f"risultati_{utente}.xlsx")
        attachment["Content-Disposition"] = f'attachment; filename="risultati_{utente}.xlsx"'
        msg.attach(attachment)

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login("infusionauxiell@gmail.com", "ubrwqtcnbyjiqach")
                server.send_message(msg)
            st.success(f"Email inviata a {email_mentor}")
        except Exception as e:
            st.error(f"Errore invio email: {e}")
