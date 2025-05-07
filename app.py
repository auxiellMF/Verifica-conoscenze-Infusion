import streamlit as st 
import pandas as pd
from io import BytesIO
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

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

    if "domande_selezionate" not in st.session_state:
        st.session_state["domande_selezionate"] = (
            df.groupby("principio", group_keys=False)
            .apply(lambda x: x.sample(n=min(2, len(x)))).reset_index(drop=True)
        )

    domande_selezionate = st.session_state["domande_selezionate"]

    utente = st.text_input("Inserisci il tuo nome")
    email = st.text_input("Inserisci l'indirizzo e-mail del tuo main mentor")

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

        if not st.session_state["submitted"]:
            if st.button("Invia Risposte"):
                if not tutte_risposte_date:
                    st.warning("⚠️ Per favore rispondi a tutte le domande prima di inviare.")
                else:
                    st.session_state["submitted"] = True

        if st.session_state["submitted"]:
            risultati_df = pd.DataFrame(risposte_date)
            punteggio = risultati_df["Esatta"].sum()
            st.success(f"Punteggio finale: {punteggio} su {len(domande_selezionate)}")

            # Genera PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            y = height - 50
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, f"Risultati del Quiz - {utente}")
            y -= 20
            c.setFont("Helvetica", 12)
            c.drawString(50, y, f"E-mail Mentor: {email}")
            y -= 30

            # Funzione per scrivere testo che va a capo
            def wrap_text(c, text, x, y, width):
                # Imposta il font per il testo
                c.setFont("Helvetica", 10)
                lines = text.split('\n')
                for line in lines:
                    text_object = c.beginText(x, y)
                    text_object.setFont("Helvetica", 10)
                    text_object.setTextOrigin(x, y)
                    text_object.textLines(line)
                    c.drawText(text_object)
                    y -= 16  # Spazio tra le righe
                return y

            # Cicla attraverso i risultati per ciascuna domanda
            for idx, r in risultati_df.iterrows():
                domanda = r["Domanda"]
                risposta = r["RispostaData"]
                corretta = r["Corretta"]
                esatta = "Giusto" if r["Esatta"] else "Sbagliato"
                
                # Scrivere la domanda in grassetto
                c.setFont("Helvetica-Bold", 12)
                y = wrap_text(c, f"Domanda: {domanda}", 50, y, width - 100)
                
                # Scrivere la risposta
                c.setFont("Helvetica", 10)
                if r["Esatta"]:
                    c.setFillColor(colors.green)  # Colore verde per la risposta corretta
                    risposta_line = f"Risposta corretta: {risposta} ({esatta})"
                else:
                    c.setFillColor(colors.black)
                    risposta_line = f"Risposta data: {risposta} ({esatta})"
                
                y = wrap_text(c, risposta_line, 50, y, width - 100)

                # Scrivere se è giusto o sbagliato
                c.setFont("Helvetica", 10)
                y = wrap_text(c, f"{esatta}", 50, y, width - 100)

                y -= 10  # spazio extra tra domande

            # Aggiungi il punteggio finale
            if y < 50:
                c.showPage()
                y = height - 50

            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.black)
            c.drawString(50, y, f"Punteggio finale: {punteggio} su {len(domande_selezionate)}")

            c.save()
            buffer.seek(0)

            st.download_button(
                label="📄 Scarica i risultati in PDF",
                data=buffer,
                file_name=f"risultati_{utente}.pdf",
                mime="application/pdf"
            )

else:
    st.error("Il file Excel deve contenere le colonne: 'principio', 'Domanda', opzioni e 'Corretta'")
