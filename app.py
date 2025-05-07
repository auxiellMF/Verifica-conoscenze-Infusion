import streamlit as st
import pandas as pd

st.title("Quiz da Excel - Verifica Conoscenze")

# Caricamento automatico del file Excel dal repository
file_path = "questionario conoscenze infusion.xlsx"

try:
    df = pd.read_excel(file_path)
    st.success("File Excel caricato automaticamente dal repository!")
except FileNotFoundError:
    st.error(f"File non trovato: {file_path}")
    st.stop()

# Verifica colonne essenziali
if "principio" in df.columns and "Domanda" in df.columns and "Corretta" in df.columns:
    utente = st.text_input("Inserisci il tuo nome")

    if utente:
        risposte_date = []
        punteggio = 0

        for idx, row in df.iterrows():
            st.markdown(f"### {row['Domanda']}")

            # Estrai dinamicamente tutte le opzioni non vuote
            opzioni = []
            for col in df.columns:
                if "opzione" in col.lower() and pd.notna(row[col]):
                    opzioni.append(str(row[col]))

            # Mostra le opzioni
            risposta = st.radio(f"Argomento: {row['principio']}", opzioni, key=idx)

            # Supporta più risposte corrette (es: "A;B;C")
            corrette = [c.strip() for c in str(row["Corretta"]).split(";")]
            esatta = risposta.strip() in corrette

            risposte_date.append({
                "Argomento": row["principio"],
                "Domanda": row["Domanda"],
                "RispostaData": risposta,
                "Corretta": row["Corretta"],
                "Esatta": esatta
            })

        # Mostra il punteggio finale e salva i risultati
        if st.button("Invia Risposte"):
            risultati_df = pd.DataFrame(risposte_date)
            punteggio = risultati_df["Esatta"].sum()
            st.success(f"Punteggio finale: {punteggio} su {len(df)}")

            risultati_df["Utente"] = utente
            risultati_df.to_excel(f"risultati_{utente}.xlsx", index=False)
            st.success("Risultati salvati in un file Excel nella cartella dell'app!")
else:
    st.error("Il file Excel deve contenere le colonne: 'principio', 'Domanda', opzioni e 'Corretta'")
