# Manuale di installazione

**Progetto:** Quiz Online — Progetto #2 (Caso A: Ristrutturazione con Python/Django e Bootstrap)
**Gruppo:** BP Solutions — Codice progetto 120
**Corso:** Programmazione Web 2025-2026

---

## 1. Cosa si sta installando

Applicazione web per la gestione di quiz online. L'applicazione permette di:

- consultare utenti, quiz e partecipazioni tramite pagine di ricerca con filtri;
- visualizzare il dettaglio di un quiz con domande e risposte;
- creare, modificare ed eliminare le partecipazioni.

L'applicazione è sviluppata in Python con il framework Django. Il database è un file SQLite già popolato, incluso nella consegna. Tutti i componenti necessari (framework, fogli di stile, caratteri) sono inclusi nella consegna: l'installazione e l'uso non richiedono connessione a internet.

## 2. Prerequisiti

- Python versione 3.12 o superiore, già presente sulla macchina di verifica.
- Un terminale: Prompt dei comandi o PowerShell su Windows; Terminale su macOS e Linux.

Nessun altro software è richiesto. Non usare alcun ambiente di sviluppo.

## 3. Procedura di installazione

1. Estrarre l'archivio `BPSolutions_Progetto2.zip` in una cartella a scelta.

2. Aprire il terminale ed entrare nella cartella estratta:

   ```
   cd percorso/di/estrazione/BPSolutions_Progetto2
   ```

   Sostituire `percorso/di/estrazione` con il percorso reale.

3. Creare l'ambiente virtuale Python:

   - **Windows:**
     ```
     python -m venv venv
     ```
   - **macOS / Linux:**
     ```
     python3 -m venv venv
     ```

4. Attivare l'ambiente virtuale:

   - **Windows (Prompt dei comandi):**
     ```
     venv\Scripts\activate
     ```
   - **Windows (PowerShell):**
     ```
     venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```
     source venv/bin/activate
     ```

   Dopo l'attivazione il prompt mostra il prefisso `(venv)`.

5. Installare il framework Django dai pacchetti inclusi nella consegna (cartella `wheels`, nessun accesso a internet richiesto):

   ```
   pip install --no-index --find-links wheels -r requirements.txt
   ```

6. Avviare il server:

   ```
   python manage.py runserver
   ```

   Il server è attivo quando compare la riga:
   `Starting development server at http://127.0.0.1:8000/`

7. Aprire il browser all'indirizzo:

   ```
   http://127.0.0.1:8000/
   ```

   La pagina iniziale dell'applicazione mostra le statistiche del database.

## 4. Verifica del funzionamento

1. Nella barra di navigazione a sinistra, premere **Utenti**: compare la tabella degli utenti con i filtri di ricerca.
2. Premere **Quiz**, poi premere il titolo di un quiz: compare il dettaglio con domande e risposte.
3. Premere **Partecipazioni**, poi **Nuova partecipazione**: compare il modulo di creazione. Le operazioni di modifica ed eliminazione sono disponibili nella colonna **Azioni** della tabella.

## 5. Arresto dell'applicazione

1. Tornare al terminale.
2. Premere `CTRL + C`: il server si arresta.
3. Digitare `deactivate` per uscire dall'ambiente virtuale.

## 6. Cosa fare se qualcosa va male

**Il comando `python3` (o `python`) non viene riconosciuto.**
Python non è nel PATH di sistema. Su Windows provare il comando `py -m venv venv`. In alternativa verificare l'installazione di Python con `python --version` oppure `py --version`.

**Il comando `pip install` fallisce.**
Verificare che l'ambiente virtuale sia attivo (prefisso `(venv)` nel prompt). Verificare che il comando sia eseguito nella cartella estratta, dove sono presenti la cartella `wheels` e il file `requirements.txt`.

**PowerShell blocca l'attivazione dell'ambiente virtuale ("esecuzione script disabilitata").**
Usare il Prompt dei comandi al posto di PowerShell, oppure eseguire in PowerShell:

```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

e ripetere il passo 4.

**All'avvio compare "Error: That port is already in use".**
La porta 8000 è occupata da un altro programma. Avviare il server su una porta diversa:

```
python manage.py runserver 8080
```

e aprire il browser su `http://127.0.0.1:8080/`.

**Il browser mostra "Impossibile raggiungere il sito".**
Verificare che il server sia in esecuzione nel terminale (riga `Starting development server`). Verificare che l'indirizzo digitato sia `http://127.0.0.1:8000/` (non `https`).

**Le pagine compaiono senza colori né impaginazione.**
Arrestare il server con `CTRL + C` e riavviarlo con `python manage.py runserver`. Ricaricare la pagina con `CTRL + F5` (Windows) oppure `CMD + MAIUSC + R` (macOS).