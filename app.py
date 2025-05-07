import streamlit as st 
import pandas as pd
from io import BytesIO
import random

st.title("Quiz da Excel - Verifica Conoscenze")

# Inizializza lo stato se non è ancora presente
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

file_path = "questionario conoscenze infusion.xlsx"

try:
    df = pd.read_excel(file_path)
    st.success("File Excel caricato automaticamente dal repository!")
except FileNotFoundError:
    st.error(f"File non trovato: {file_path}")
    st.stop()

# Verifica colonne essenziali
if "principio" in df.columns and "Domanda" in df.columns and "Corretta" in df.columns:

    # Estrai domande solo una volta
    if "domande_selezionate" not in st.session_state:
        st.session_state["domande_selezionate"] = (
            df.groupby("principio", group_keys=False)
            .apply(lambda x: x.sample(n=min(2, len(x))))
            .reset_index(drop=True)
        )

    domande_selezionate = st.session_state["domande_selezionate"]

    utente = st.text_input("Inserisci il tuo nome")
    email = st.text_input("Inserisci il tuo indirizzo email")

    if utente and email:
        risposte_date = []
        tutte_risposte_date = True

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

            risposte_date.append({
                "Argomento": row["principio"],
                "Domanda": row["Domanda"],
                "RispostaData": risposta,
                "Corretta": row["Corretta"],
                "Esatta": risposta in [c.strip() for c in str(row["Corretta"]).split(";")] if risposta else False
            })

        # (if not st.session_state["submitted"]:
            if st.button("Invia Risposte"):
                if not tutte_risposte_date:
                    st.warning("⚠️ Per favore rispondi a tutte le domande prima di inviare.")
                else:
                    st.session_state["submitted"] = True)

        if st.session_state["submitted"]:
            risultati_df = pd.DataFrame(risposte_date)
            punteggio = risultati_df["Esatta"].sum()
            st.success(f"Punteggio finale: {punteggio} su {len(domande_selezionate)}")

            risultati_df["Utente"] = utente
            risultati_df["Email"] = email

            output = BytesIO()
            risultati_df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            st.download_button(
                label="📥 Scarica i risultati in Excel",
                data=output,
                file_name=f"risultati_{utente}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.error("Il file Excel deve contenere le colonne: 'principio', 'Domanda', opzioni e 'Corretta'")
