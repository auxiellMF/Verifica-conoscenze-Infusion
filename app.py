import streamlit as st
import pandas as pd

st.title("Quiz da Excel")

# Caricamento file
df = pd.read_excel("questionario conoscenze infusion.xlsx")
st.success("File Excel caricato automaticamente dal repository!")


    # Verifica che ci siano le colonne richieste
    if "principio" in df.columns and "Domanda" in df.columns and "Corretta" in df.columns:
        utente = st.text_input("Inserisci il tuo nome")

        if utente:
            risposte_date = []
            punteggio = 0

            for idx, row in df.iterrows():
                st.markdown(f"### {row['Domanda']}")

                # Estrai opzioni dinamicamente
                opzioni = []
                for col in df.columns:
                    if "opzione" in col.lower() and pd.notna(row[col]):
                        opzioni.append(str(row[col]))

                risposta = st.radio(f"Argomento: {row['principio']}", opzioni, key=idx)

                # Gestione risposte multiple nella colonna "Corretta"
                corrette = [c.strip() for c in str(row["Corretta"]).split(";")]
                esatta = risposta.strip() in corrette

                risposte_date.append({
                    "Argomento": row["principio"],
                    "Domanda": row["Domanda"],
                    "RispostaData": risposta,
                    "Corretta": row["Corretta"],
                    "Esatta": esatta
                })

            if st.button("Invia Risposte"):
                risultati_df = pd.DataFrame(risposte_date)
                punteggio = risultati_df["Esatta"].sum()
                st.success(f"Punteggio finale: {punteggio} su {len(df)}")

                risultati_df["Utente"] = utente
                risultati_df.to_excel(f"risultati_{utente}.xlsx", index=False)
                st.success("Risultati salvati in un file Excel!")
    else:
        st.error("Il file deve avere almeno le colonne: principio, Domanda, opzione..., Corretta")
