import streamlit as st  
import pandas as pd
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime

st.set_page_config(page_title="Quiz auxiell", layout="centered")

# Logo fisso
st.markdown("""
    <style>
    .fixed-logo-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: white;
        text-align: center;
        padding-top: 65px;
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

st.title("Verifica competenze Infusion")

# Stato iniziale
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "proseguito" not in st.session_state:
    st.session_state["proseguito"] = False
if "azienda_scelta" not in st.session_state:
    st.session_state["azienda_scelta"] = None
if "email_inviata" not in st.session_state:
    st.session_state["email_inviata"] = False

# Caricamento Excel
file_path = "questionario conoscenze infusion.xlsx"
try:
    df = pd.read_excel(file_path)
    st.success("Domande pronte!")
except FileNotFoundError:
    st.error(f"File non trovato: {file_path}")
    st.stop()

# Verifica colonne necessarie
required_cols = ["Azienda", "principio", "Domanda", "Corretta", "opzione 1"]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    st.error(f"Mancano le colonne obbligatorie: {', '.join(missing)}")
    st.stop()

# Colonne opzione
option_cols = [c for c in df.columns if c.lower().strip().startswith("opzione")]
if not option_cols:
    st.error("Nessuna colonna di opzione trovata.")
    st.stop()

# Step 1: selezione azienda
if st.session_state["azienda_scelta"] is None:
    aziende_disponibili = sorted(df["Azienda"].dropna().unique())
    azienda_scelta = st.selectbox("Seleziona la tua azienda", aziende_disponibili)
    if st.button("Conferma azienda"):
        st.session_state["azienda_scelta"] = azienda_scelta
    st.stop()

# Step 2: filtro domande per azienda
azienda_scelta = st.session_state["azienda_scelta"]

# Applica tema scuro ogni volta se l'azienda è stata scelta
st.markdown("""
    <style>
    body, .stApp {
        background-color: #000 !important;
        color: white !important;
    }
    .css-1v0mbdj, .stTextInput input, .stSelectbox div, .stRadio div, .stMultiSelect div {
        background-color: #333 !important;
        color: white !important;
    }
    label, .stRadio label, .stMultiSelect label {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

df_filtrato = df[df["Azienda"] == azienda_scelta]

if "domande_selezionate" not in st.session_state:
    st.session_state["domande_selezionate"] = (
        df_filtrato.groupby("principio", group_keys=False)
                   .apply(lambda x: x.sample(n=min(2, len(x))))
                   .reset_index(drop=True)
    )
domande = st.session_state["domande_selezionate"]

utente = st.text_input("Inserisci il tuo nome")
email_compilatore = st.text_input("Inserisci la tua email aziendale")
email_mentor = st.text_input("Inserisci l'indirizzo e-mail del tuo main mentor")

errore_email = None
dominio_atteso = {
    "auxiell": "@auxiell.com",
    "euxilia": "@euxilia.com",
    "xva": "@xva-services.com"
}
dominio = dominio_atteso.get(azienda_scelta.lower(), "@auxiell.com")

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

    for idx, row in domande.iterrows():
        st.markdown(f"**{row['Domanda']}**")
        if pd.isna(row["opzione 1"]):
            ans = st.text_input(f"Risposta libera ({row['principio']})", key=f"open_{idx}", disabled=st.session_state["submitted"])
            risposte.append({
                "Tipo": "aperta",
                "Azienda": azienda_scelta,
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
                "Azienda": azienda_scelta,
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
    info = pd.DataFrame([{ "Nome": utente, "Data": data_test, "Punteggio": f"{perc}%", "Azienda": azienda_scelta }])
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
