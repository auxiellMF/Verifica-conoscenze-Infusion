import streamlit as st 
import pandas as pd
from io import BytesIO

st.title("Quiz da Excel - Verifica Conoscenze")

file_path = "questionario conoscenze infusion.xlsx"

try:
    df = pd.read_excel(file_path)
    st.success("File Excel caricato automaticamente dal repository!")
except FileNotFoundError:
    st.error(f"File non trovato: {file_path}")
    st.stop()

if "principio" in df.columns and "Domanda" in df.columns and "Corretta" in df.columns:

    domande_selezionate = (
        df.groupby("principio", group_keys=False)
        .apply(lambda x: x.sample(n=min(2, len(x)), random_state=42))
        .reset_index(drop=True)
    )

    utente = st.text_input("Inserisci il tuo nome")

    if utente:
        risposte_date = []
        punteggio = 0

        for idx, row in domande_selezionate.iterrows():
            st.markdown(f"### {row['Domanda']}")

            opzioni = ["-- Seleziona un'opzione --"]
            for col in df.columns:
                if "opzione" in col.lower() and pd.notna(row[col]):
                    opzioni.append(str(row[col]))

            key_radio = f"risposta_{idx}"
            risposta = st.radio(
                f"Argomento: {row['principio']}",
                opzioni,
                key=key_radio,
                index=0
            )

            # Pulsante "Cancella risposta"
            if st.button("🧹 Cancella risposta", key=f"cancella_{idx}"):
                st.session_state[key_radio] = "-- Seleziona un'opzione --"

            corrette = [c.strip() for c in str(row["Corretta"]).split(";")]
            esatta = risposta.strip() in corrette if risposta != "-- Seleziona un'opzione --" else False

            risposte_date.append({ 
                "Argomento": row["principio"],
                "Domanda": row["Domanda"],
                "RispostaData": risposta if risposta != "-- Seleziona un'opzione --" else "",
                "Corretta": row["Corretta"],
                "Esatta": esatta
            })

        if st.button("Invia Risposte"):
            risultati_df = pd.DataFrame(risposte_date)
            punteggio = risultati_df["Esatta"].sum()
            st.success(f"Punteggio finale: {punteggio} su {len(domande_selezionate)}")

            risultati_df["Utente"] = utente

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
