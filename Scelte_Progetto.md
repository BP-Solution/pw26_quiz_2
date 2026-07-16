# Scelte di progetto

**Quiz Online — Progetto #2 — Gruppo BP Solutions (codice 120) — Programmazione Web 2025-2026**

---

## Scelta progettuale: Caso A — Ristrutturazione

Il gruppo ha scelto la ristrutturazione del primo progetto con la tecnologia **Python → Django e Bootstrap**. Il primo progetto (PHP e MySQL su Altervista) è stato riscritto come applicazione Django mantenendo le stesse funzionalità: pagine di ricerca con filtri per Utenti, Quiz e Partecipazioni, pagina di dettaglio del quiz con domande e risposte, e operazioni CRUD complete sulla tabella assegnata Partecipazione, con validazione dei dati e messaggi di esito. L'interfaccia replica il layout assegnato (Interfaccia 3) e la palette Beige del primo progetto, riutilizzando il foglio di stile originale del gruppo.

## Database: SQLite

Per la consegna è stato scelto SQLite al posto di MySQL. Motivazione: SQLite è integrato in Python e non richiede l'installazione né la configurazione di un server di database sulla macchina di verifica. Il file `db.sqlite3`, già popolato con dati sintetici (1000 utenti, 300 quiz con relative domande e risposte, 8000 partecipazioni), è incluso nella consegna: l'installazione si riduce alla creazione dell'ambiente virtuale e all'avvio del server, senza rieseguire il seed. Il dataset include volutamente anche casi limite: quiz senza domande, quiz senza partecipazioni e quiz con un numero di domande molto elevato. Lo schema conserva i vincoli del database originale: le chiavi composte sono espresse con vincoli di unicità (`unique_together`) e il vincolo sul punteggio (valorizzato solo per le risposte di tipo Corretta) è garantito dalla logica applicativa, come nel primo progetto.

## Struttura dell'applicazione

Il progetto Django è composto da un unico progetto (`quizsite`) con una sola app (`quiz`) che contiene i sei modelli ORM corrispondenti alle entità dello schema (Utente, Quiz, Domanda, Risposta, Partecipazione, RispostaUtenteQuiz), le viste, i template e i file statici. I dati sintetici sono generati da un comando di gestione dedicato (`genera_seed`), che riusa la logica di popolamento massivo sviluppata per il primo progetto convertita all'ORM di Django.

## Bootstrap e foglio di stile del gruppo

Bootstrap 5.3 è incluso come base dei componenti e della normalizzazione tra browser; il foglio di stile personalizzato del gruppo è caricato dopo Bootstrap, in modo da mantenere l'identità visiva del primo progetto (palette Beige, tipografia Playfair Display e Source Sans 3, layout Interfaccia 3).

## Funzionamento completamente offline

Per garantire l'installazione entro cinque minuti anche in assenza di connessione, tutte le risorse esterne sono incluse nella consegna: Bootstrap e i caratteri tipografici sono serviti come file statici locali, e i pacchetti Python necessari (Django e dipendenze) sono forniti nella cartella `wheels` e installati con pip in modalità locale (`--no-index`), senza accesso alla rete.