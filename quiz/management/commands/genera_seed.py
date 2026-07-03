# Quiz Online - Progetto #2, gruppo BP Solutions
# Comando di management "genera_seed": popola il database con dati sintetici
# (utenti, quiz, domande, risposte, partecipazioni) per demo e test manuali.
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from quiz.models import (
    Utente,
    Quiz,
    Domanda,
    Risposta,
    Partecipazione,
    RispostaUtenteQuiz,
)


# ── CONFIGURAZIONE ──────────────────────────────────────────
N_UTENTI        = 30
N_QUIZ          = 50
MIN_DOMANDE     = 3
MAX_DOMANDE     = 8
MIN_RISPOSTE    = 3
MAX_RISPOSTE    = 5
MIN_PART        = 3   # partecipazioni minime per utente
MAX_PART        = 8   # partecipazioni massime per utente
# ────────────────────────────────────────────────────────────

# Pool di nomi e cognomi usati per generare gli utenti sintetici.
nomi    = ["Marco","Luca","Sara","Giulia","Andrea","Matteo","Anna","Chiara",
           "Paolo","Elena","Davide","Francesca","Simone","Laura","Roberto",
           "Valentina","Stefano","Alice","Giorgio","Marta","Nicola","Beatrice",
           "Fabio","Silvia","Lorenzo","Federica","Daniele","Elisa","Riccardo","Sofia"]

cognomi = ["Rossi","Bianchi","Verdi","Ferrari","Esposito","Romano","Colombo",
           "Ricci","Marino","Greco","Bruno","Conti","De Luca","Mancini","Costa",
           "Giordano","Rizzo","Lombardi","Moretti","Barbieri","Fontana","Santoro",
           "Mariani","Rinaldi","Caruso","Ferrara","Gallo","Hart","Martini","Leone"]

# Temi usati per comporre i titoli dei quiz generati.
temi_quiz = ["SQL Base","Python Avanzato","Reti di Calcolatori","Algoritmi",
             "Basi di Dati","Programmazione Web","Sistemi Operativi","Java OOP",
             "Matematica Discreta","Sicurezza Informatica","HTML e CSS","JavaScript",
             "PHP e MySQL","Linux","Cloud Computing","Machine Learning","UML",
             "Architettura dei Computer","Ingegneria del Software","React"]

# Testi delle domande realistiche assegnate ai quiz, a rotazione.
testi_domande = [
    "Cosa si intende per chiave primaria?",
    "Qual è la differenza tra DELETE e TRUNCATE?",
    "Cosa fa l'istruzione JOIN?",
    "Cos'è una foreign key?",
    "Cosa significa normalizzazione?",
    "Cosa fa il comando SELECT DISTINCT?",
    "Cosa è un indice in un database?",
    "Cosa si intende per transazione?",
    "Cosa fa GROUP BY?",
    "Cosa è una vista (VIEW)?",
    "Cosa fa HAVING?",
    "Qual è la differenza tra WHERE e HAVING?",
    "Cosa si intende per OOP?",
    "Cosa è un costruttore?",
    "Cosa fa il polimorfismo?",
    "Cosa è l'ereditarietà?",
    "Cosa è un'interfaccia in Java?",
    "Cosa fa il ciclo while?",
    "Cosa è una variabile locale?",
    "Cosa è una funzione ricorsiva?",
    "Cosa fa il protocollo HTTP?",
    "Cosa è un indirizzo IP?",
    "Cosa è il DNS?",
    "Cosa fa il protocollo TCP?",
    "Cosa è un socket?",
    "Cosa è il modello OSI?",
    "Cosa fa CSS?",
    "Cosa è il DOM?",
    "Cosa fa AJAX?",
    "Cosa è una Promise in JavaScript?",
]

# Banca di risposte corrette/sbagliate specifiche per ciascuna domanda nota,
# usata da scegli_risposte per generare contenuti coerenti col testo della domanda.
risposte_per_domanda = {
    "Cosa si intende per chiave primaria?": {
        "Corretta": [
            "Un attributo o insieme di attributi che identifica univocamente ogni record della tabella",
            "Una colonna che non ammette valori duplicati e serve a distinguere ogni riga",
            "Il vincolo usato per rendere univoca l'identificazione delle tuple",
            "Una chiave candidata scelta per identificare in modo stabile i record",
        ],
        "Sbagliata": [
            "Una colonna che può contenere duplicati ma velocizza gli ordinamenti",
            "La chiave usata solo per collegarsi a una tabella esterna",
            "Un campo facoltativo che può essere NULL in molte righe",
            "La password necessaria per accedere al database",
            "Un indice creato automaticamente su tutte le colonne testuali",
        ],
    },
    "Qual è la differenza tra DELETE e TRUNCATE?": {
        "Corretta": [
            "DELETE elimina righe selezionabili con WHERE, TRUNCATE svuota rapidamente tutta la tabella",
            "DELETE opera sulle righe, mentre TRUNCATE rimuove tutti i dati della tabella in modo più diretto",
            "DELETE può cancellare solo alcune righe, TRUNCATE cancella l'intero contenuto",
            "TRUNCATE di solito reimposta anche contatori automatici, DELETE no",
        ],
        "Sbagliata": [
            "DELETE cancella la struttura della tabella, TRUNCATE cancella solo una colonna",
            "DELETE serve per aggiungere righe, TRUNCATE per modificarle",
            "TRUNCATE filtra le righe con WHERE meglio di DELETE",
            "DELETE funziona solo sulle viste, TRUNCATE solo sugli indici",
            "Sono due nomi diversi per lo stesso identico comando",
        ],
    },
    "Cosa fa l'istruzione JOIN?": {
        "Corretta": [
            "Combina righe provenienti da due o più tabelle in base a una condizione",
            "Permette di interrogare dati correlati presenti in tabelle diverse",
            "Unisce risultati usando relazioni tra colonne, ad esempio chiavi primarie ed esterne",
            "Restituisce una tabella risultato composta da dati collegati tra loro",
        ],
        "Sbagliata": [
            "Elimina definitivamente le righe duplicate da una tabella",
            "Crea una nuova tabella fisica con lo stesso schema",
            "Ordina i record in base a una colonna numerica",
            "Converte una tabella relazionale in un file JSON",
            "Aggiunge automaticamente una chiave primaria a ogni tabella",
        ],
    },
    "Cos'è una foreign key?": {
        "Corretta": [
            "Un vincolo che collega una colonna ai valori di una chiave in un'altra tabella",
            "Una chiave esterna che mantiene la coerenza tra tabelle correlate",
            "Un riferimento alla chiave primaria o candidata di un'altra tabella",
            "Un campo usato per rappresentare una relazione tra record di tabelle diverse",
        ],
        "Sbagliata": [
            "Una chiave primaria scritta in una lingua straniera",
            "Un indice temporaneo creato solo durante una query",
            "Una colonna che contiene sempre valori casuali",
            "Il nome del server remoto che ospita il database",
            "Una password condivisa tra due database",
        ],
    },
    "Cosa significa normalizzazione?": {
        "Corretta": [
            "Organizzare le tabelle per ridurre ridondanze e anomalie nei dati",
            "Applicare regole progettuali per migliorare coerenza e struttura del database",
            "Separare i dati in tabelle correlate evitando ripetizioni inutili",
            "Portare uno schema verso forme normali come 1NF, 2NF e 3NF",
        ],
        "Sbagliata": [
            "Convertire tutti i testi in lettere minuscole",
            "Aumentare volontariamente la duplicazione per velocizzare ogni query",
            "Cancellare tutte le relazioni tra le tabelle",
            "Rinominare le colonne usando solo numeri progressivi",
            "Comprimere il database in un archivio zip",
        ],
    },
    "Cosa fa il comando SELECT DISTINCT?": {
        "Corretta": [
            "Restituisce solo combinazioni di valori non duplicate nel risultato",
            "Elimina i duplicati dal risultato della SELECT",
            "Mostra una sola volta le righe uguali rispetto alle colonne selezionate",
            "Produce un elenco di valori distinti per le colonne richieste",
        ],
        "Sbagliata": [
            "Cancella i duplicati dalla tabella originale",
            "Ordina sempre i risultati in ordine alfabetico",
            "Seleziona solo le righe con valori NULL",
            "Crea una chiave primaria sulle colonne indicate",
            "Mostra solo la prima colonna della tabella",
        ],
    },
    "Cosa è un indice in un database?": {
        "Corretta": [
            "Una struttura dati che velocizza la ricerca delle righe",
            "Un meccanismo usato per trovare record più rapidamente su una o più colonne",
            "Una struttura ausiliaria che migliora alcune query di lettura",
            "Un'organizzazione dei valori che rende più efficiente l'accesso ai dati",
        ],
        "Sbagliata": [
            "Una tabella che contiene sempre il conteggio totale delle righe",
            "Un commento descrittivo salvato accanto alla query",
            "Una copia completa del database usata per il backup",
            "Il numero massimo di utenti collegabili al server",
            "Un tipo di dato usato solo per memorizzare immagini",
        ],
    },
    "Cosa si intende per transazione?": {
        "Corretta": [
            "Un insieme di operazioni eseguite come un'unica unita logica",
            "Una sequenza di modifiche che deve completarsi tutta oppure essere annullata",
            "Un blocco di lavoro che rispetta proprieta come atomicita e consistenza",
            "Un'operazione composta che puo essere confermata con COMMIT o annullata con ROLLBACK",
        ],
        "Sbagliata": [
            "Una singola SELECT che non modifica mai dati",
            "Un trasferimento di file tra due computer della rete",
            "La creazione automatica di un nuovo utente",
            "Una tabella temporanea usata solo per i report",
            "Un indice speciale sui campi numerici",
        ],
    },
    "Cosa fa GROUP BY?": {
        "Corretta": [
            "Raggruppa le righe che hanno gli stessi valori in una o piu colonne",
            "Permette di calcolare aggregazioni separate per gruppi di record",
            "Divide il risultato in gruppi su cui usare funzioni come COUNT o SUM",
            "Aggrega le righe in base alle colonne specificate",
        ],
        "Sbagliata": [
            "Ordina sempre le righe dal valore piu piccolo al piu grande",
            "Elimina fisicamente i gruppi duplicati dalla tabella",
            "Crea gruppi di utenti con permessi diversi",
            "Unisce due tabelle come farebbe una JOIN",
            "Mostra solo le righe con valori NULL",
        ],
    },
    "Cosa è una vista (VIEW)?": {
        "Corretta": [
            "Una query salvata che si puo interrogare come se fosse una tabella",
            "Una rappresentazione logica dei dati basata su una SELECT",
            "Un oggetto del database che espone un risultato derivato da una query",
            "Una tabella virtuale costruita a partire da una o piu tabelle",
        ],
        "Sbagliata": [
            "Una copia fisica obbligatoria di tutti i dati",
            "La schermata grafica del programma di amministrazione",
            "Un tipo di indice usato per criptare le password",
            "Un file immagine associato a una tabella",
            "Un comando che cancella una tabella dal database",
        ],
    },
    "Cosa fa HAVING?": {
        "Corretta": [
            "Filtra i gruppi prodotti da GROUP BY",
            "Applica condizioni sui risultati aggregati",
            "Permette di limitare gruppi in base a funzioni come COUNT o AVG",
            "Seleziona solo i gruppi che soddisfano una condizione",
        ],
        "Sbagliata": [
            "Filtra le singole righe prima del raggruppamento come WHERE",
            "Crea automaticamente una nuova tabella aggregata",
            "Ordina i gruppi in ordine decrescente",
            "Serve solo per verificare se una colonna e NULL",
            "Sostituisce SELECT nelle query con aggregazioni",
        ],
    },
    "Qual è la differenza tra WHERE e HAVING?": {
        "Corretta": [
            "WHERE filtra le righe prima dell'aggregazione, HAVING filtra i gruppi dopo",
            "WHERE lavora sui record, HAVING sui risultati aggregati",
            "WHERE si applica prima di GROUP BY, HAVING dopo il raggruppamento",
            "HAVING puo usare condizioni su COUNT o SUM, WHERE filtra dati di partenza",
        ],
        "Sbagliata": [
            "WHERE si usa solo con le tabelle, HAVING solo con gli utenti",
            "HAVING filtra prima le righe e WHERE filtra dopo i gruppi",
            "Sono sempre intercambiabili in qualunque query",
            "WHERE serve per ordinare, HAVING per cancellare",
            "HAVING funziona solo senza GROUP BY e WHERE solo con GROUP BY",
        ],
    },
    "Cosa si intende per OOP?": {
        "Corretta": [
            "Programmazione orientata agli oggetti, basata su classi e oggetti",
            "Un paradigma che organizza il codice attorno a oggetti con stato e comportamento",
            "Un modo di progettare software usando incapsulamento, ereditarieta e polimorfismo",
            "Una tecnica che modella entita tramite classi, attributi e metodi",
        ],
        "Sbagliata": [
            "Un protocollo di rete per trasferire pagine web",
            "Un linguaggio specifico alternativo a Java",
            "Una tecnica per scrivere query SQL piu brevi",
            "Un algoritmo di ordinamento stabile",
            "Un formato immagine vettoriale per il web",
        ],
    },
    "Cosa è un costruttore?": {
        "Corretta": [
            "Un metodo speciale chiamato quando viene creato un oggetto",
            "Una funzione usata per inizializzare lo stato iniziale di un'istanza",
            "Il blocco di codice che prepara un nuovo oggetto della classe",
            "Un metodo con responsabilita di inizializzazione dell'oggetto",
        ],
        "Sbagliata": [
            "Un metodo che distrugge sempre l'oggetto a fine programma",
            "Una classe astratta che non puo avere attributi",
            "Una variabile globale condivisa da tutte le classi",
            "Un ciclo che crea automaticamente infinite istanze",
            "Un file di configurazione del compilatore",
        ],
    },
    "Cosa fa il polimorfismo?": {
        "Corretta": [
            "Permette a oggetti diversi di rispondere allo stesso metodo in modi diversi",
            "Consente di trattare oggetti differenti tramite una stessa interfaccia",
            "Rende possibile ridefinire o specializzare comportamenti nelle classi derivate",
            "Fa si che lo stesso messaggio produca comportamenti diversi a seconda dell'oggetto",
        ],
        "Sbagliata": [
            "Trasforma automaticamente un oggetto in una tabella SQL",
            "Impedisce a due classi di avere metodi con lo stesso nome",
            "Cancella tutti gli attributi ereditati da una classe",
            "Serve solo per comprimere il codice sorgente",
            "Permette a una variabile di cambiare nome durante l'esecuzione",
        ],
    },
    "Cosa è l'ereditarietà?": {
        "Corretta": [
            "Un meccanismo con cui una classe puo derivare attributi e metodi da un'altra",
            "La relazione che permette a una sottoclasse di riusare e specializzare una superclasse",
            "Un modo per modellare classi piu specifiche a partire da classi generali",
            "La capacita di una classe figlia di ottenere comportamento dalla classe padre",
        ],
        "Sbagliata": [
            "La copia manuale del codice da un file a un altro",
            "La possibilita di ereditare dati da un database remoto",
            "Un vincolo SQL tra due tabelle",
            "Il salvataggio automatico degli oggetti su disco",
            "Una funzione che ordina classi in base al nome",
        ],
    },
    "Cosa è un'interfaccia in Java?": {
        "Corretta": [
            "Un contratto che dichiara metodi che una classe puo implementare",
            "Un tipo che definisce comportamenti attesi senza fissare tutta l'implementazione",
            "Una struttura usata per specificare metodi comuni a classi diverse",
            "Un riferimento che permette di programmare rispetto a un contratto",
        ],
        "Sbagliata": [
            "La finestra grafica obbligatoria di ogni programma Java",
            "Una classe che contiene solo variabili private modificabili",
            "Un costruttore speciale usato per avviare la JVM",
            "Un file CSS collegato a una servlet",
            "Una tabella che collega Java a MySQL",
        ],
    },
    "Cosa fa il ciclo while?": {
        "Corretta": [
            "Ripete un blocco di istruzioni finche una condizione resta vera",
            "Esegue codice piu volte controllando la condizione prima di ogni iterazione",
            "Continua a iterare finche l'espressione booleana non diventa falsa",
            "Permette ripetizioni basate su una condizione logica",
        ],
        "Sbagliata": [
            "Esegue sempre il blocco una sola volta",
            "Definisce una funzione ricorsiva senza parametri",
            "Serve a importare librerie esterne",
            "Ordina automaticamente un array",
            "Crea una nuova classe a ogni iterazione",
        ],
    },
    "Cosa è una variabile locale?": {
        "Corretta": [
            "Una variabile dichiarata dentro un blocco, metodo o funzione",
            "Una variabile visibile solo nell'ambito in cui e stata definita",
            "Un dato temporaneo accessibile soltanto nello scope locale",
            "Una variabile la cui vita e limitata all'esecuzione del blocco o metodo",
        ],
        "Sbagliata": [
            "Una variabile salvata sempre nel database locale",
            "Una costante disponibile in tutto il programma",
            "Una variabile accessibile da qualunque classe senza import",
            "Il nome del computer su cui gira il programma",
            "Un parametro di rete della macchina",
        ],
    },
    "Cosa è una funzione ricorsiva?": {
        "Corretta": [
            "Una funzione che richiama se stessa per risolvere un problema",
            "Una funzione definita tramite uno o piu casi base e chiamate a se stessa",
            "Una procedura che scompone il problema in versioni piu piccole dello stesso problema",
            "Un algoritmo espresso con chiamate ripetute alla stessa funzione",
        ],
        "Sbagliata": [
            "Una funzione che non puo avere parametri",
            "Una funzione eseguita automaticamente dal sistema operativo",
            "Un ciclo while scritto con una sintassi diversa",
            "Una query SQL che richiama una tabella esterna",
            "Una funzione che restituisce sempre un valore casuale",
        ],
    },
    "Cosa fa il protocollo HTTP?": {
        "Corretta": [
            "Regola lo scambio di richieste e risposte tra client web e server",
            "Permette al browser di richiedere risorse come pagine, immagini e API",
            "Definisce metodi come GET e POST per comunicare sul web",
            "Stabilisce il formato della comunicazione applicativa tra browser e server",
        ],
        "Sbagliata": [
            "Assegna indirizzi IP ai dispositivi della rete locale",
            "Cripta sempre tutti i dati senza bisogno di TLS",
            "Traduce nomi di dominio in indirizzi IP",
            "Gestisce direttamente il routing dei pacchetti Internet",
            "Compila il codice JavaScript nel browser",
        ],
    },
    "Cosa è un indirizzo IP?": {
        "Corretta": [
            "Un identificatore numerico assegnato a un dispositivo in rete",
            "L'indirizzo logico usato per instradare pacchetti tra host",
            "Un valore IPv4 o IPv6 che identifica un'interfaccia di rete",
            "Un riferimento di rete usato per raggiungere un dispositivo",
        ],
        "Sbagliata": [
            "Il nome leggibile di un sito, come esempio.it",
            "La password del router Wi-Fi",
            "Il codice HTML di una pagina web",
            "Un protocollo per inviare email",
            "Il numero seriale fisico della scheda madre",
        ],
    },
    "Cosa è il DNS?": {
        "Corretta": [
            "Il sistema che traduce nomi di dominio in indirizzi IP",
            "Un servizio distribuito per risolvere nomi come esempio.it",
            "La rubrica di Internet che associa domini e indirizzi",
            "Un'infrastruttura gerarchica per la risoluzione dei nomi",
        ],
        "Sbagliata": [
            "Un linguaggio di programmazione per server web",
            "Un protocollo che cripta automaticamente tutte le connessioni",
            "Il database locale delle password degli utenti",
            "Una tecnica per comprimere immagini",
            "Un componente che sostituisce il browser",
        ],
    },
    "Cosa fa il protocollo TCP?": {
        "Corretta": [
            "Fornisce una comunicazione affidabile e ordinata tra applicazioni",
            "Gestisce connessioni con controllo degli errori e ritrasmissione dei segmenti",
            "Garantisce che i dati arrivino in ordine quando possibile",
            "Stabilisce una connessione logica tra due endpoint di rete",
        ],
        "Sbagliata": [
            "Traduce direttamente nomi di dominio in indirizzi IP",
            "Disegna la struttura visuale di una pagina web",
            "Memorizza permanentemente i dati in una tabella",
            "Sostituisce HTML nelle applicazioni web",
            "Crea indirizzi email per gli utenti",
        ],
    },
    "Cosa è un socket?": {
        "Corretta": [
            "Un endpoint software per comunicare in rete",
            "L'associazione tra indirizzo IP, porta e protocollo per una comunicazione",
            "Un'interfaccia usata dai programmi per inviare e ricevere dati di rete",
            "Un punto di comunicazione tra processi su host locali o remoti",
        ],
        "Sbagliata": [
            "Un tipo di cavo fisico Ethernet",
            "Una tabella speciale del database",
            "Un linguaggio per definire pagine web",
            "Un algoritmo di cifratura delle password",
            "La memoria permanente del browser",
        ],
    },
    "Cosa è il modello OSI?": {
        "Corretta": [
            "Un modello a sette livelli che descrive le funzioni della comunicazione di rete",
            "Uno schema teorico che separa la comunicazione in livelli dal fisico all'applicativo",
            "Un riferimento usato per studiare e confrontare protocolli di rete",
            "Una struttura concettuale con livelli come rete, trasporto e applicazione",
        ],
        "Sbagliata": [
            "Un database relazionale usato nei sistemi operativi",
            "Un framework JavaScript per applicazioni web",
            "Un algoritmo per ordinare pacchetti in memoria",
            "Una tecnica per normalizzare tabelle SQL",
            "Il nome di un singolo protocollo di posta elettronica",
        ],
    },
    "Cosa fa CSS?": {
        "Corretta": [
            "Definisce lo stile e la presentazione delle pagine web",
            "Controlla colori, layout, spaziature e tipografia degli elementi HTML",
            "Permette di separare contenuto HTML e aspetto grafico",
            "Applica regole visuali agli elementi del documento",
        ],
        "Sbagliata": [
            "Esegue query sul database del sito",
            "Gestisce la logica lato server in PHP",
            "Cripta automaticamente tutte le password",
            "Definisce il contenuto semantico al posto di HTML",
            "Assegna indirizzi IP ai client",
        ],
    },
    "Cosa è il DOM?": {
        "Corretta": [
            "La rappresentazione ad albero del documento HTML usata dal browser",
            "Un modello a oggetti che permette agli script di leggere e modificare la pagina",
            "La struttura in memoria degli elementi della pagina web",
            "L'interfaccia con cui JavaScript manipola il contenuto HTML",
        ],
        "Sbagliata": [
            "Un protocollo di trasporto alternativo a TCP",
            "Un database orientato agli oggetti",
            "Un selettore CSS usato solo per i colori",
            "Il nome del server che ospita una pagina",
            "Un algoritmo per comprimere file JavaScript",
        ],
    },
    "Cosa fa AJAX?": {
        "Corretta": [
            "Permette richieste asincrone al server senza ricaricare tutta la pagina",
            "Consente di aggiornare parti della pagina usando dati ricevuti dal server",
            "Usa JavaScript per comunicare con il server in background",
            "Rende possibile caricare dati dinamicamente dopo il caricamento della pagina",
        ],
        "Sbagliata": [
            "Disegna automaticamente il layout CSS di una pagina",
            "Compila codice PHP nel browser",
            "Sostituisce completamente il protocollo HTTP",
            "Cancella la cache del server a ogni richiesta",
            "Crea tabelle SQL partendo da un form HTML",
        ],
    },
    "Cosa è una Promise in JavaScript?": {
        "Corretta": [
            "Un oggetto che rappresenta il risultato futuro di un'operazione asincrona",
            "Una struttura che puo essere in stato pending, fulfilled o rejected",
            "Un modo per gestire completamento o fallimento di operazioni asincrone",
            "Un valore che sara disponibile in futuro e si gestisce con then, catch o await",
        ],
        "Sbagliata": [
            "Una variabile globale che non puo cambiare valore",
            "Una funzione eseguita solo lato server PHP",
            "Un selettore CSS per animazioni",
            "Un tipo di ciclo che ripete codice all'infinito",
            "Una tabella temporanea del database",
        ],
    },
}

# Risposte generiche di fallback, usate quando una domanda non ha una voce
# dedicata in risposte_per_domanda.
risposte_generiche = {
    "Corretta": [
        "Una definizione corretta del concetto richiesto",
        "Una spiegazione coerente con la teoria dell'argomento",
        "Una risposta precisa e pertinente alla domanda",
        "Una formulazione valida del concetto principale",
    ],
    "Sbagliata": [
        "Una definizione che confonde il concetto con un argomento diverso",
        "Una risposta non coerente con la domanda posta",
        "Una spiegazione parziale che porta a una conclusione errata",
        "Un'affermazione plausibile ma tecnicamente sbagliata",
        "Una descrizione che usa termini corretti nel contesto sbagliato",
    ],
}


def data_casuale(inizio, fine):
    """Restituisce una data casuale compresa nell'intervallo [inizio, fine]."""
    delta = (fine - inizio).days
    return inizio + timedelta(days=random.randint(0, delta))


def scegli_risposte(testo_domanda, tipo, quantita):
    """Seleziona un numero di risposte del tipo richiesto (Corretta/Sbagliata) per la
    domanda indicata, pescando dal pool specifico o da quello generico se assente;
    usa il campionamento senza ripetizioni quando possibile, altrimenti con ripetizioni."""
    pool = risposte_per_domanda.get(testo_domanda, risposte_generiche)[tipo]
    if quantita <= len(pool):
        return random.sample(pool, quantita)
    return random.choices(pool, k=quantita)



class Command(BaseCommand):
    """Comando 'genera_seed': ripopola da zero il database con un dataset
    sintetico coerente di utenti, quiz, domande, risposte e partecipazioni."""
    help = "Popola il database con dati sintetici per il sistema di quiz."

    @transaction.atomic
    def handle(self, *args, **options):
        """Esegue il seed in un'unica transazione: svuota le tabelle esistenti
        e ricrea in sequenza utenti, quiz, domande/risposte e partecipazioni."""
        # Fase 1: pulizia completa dei dati esistenti, rispettando l'ordine
        # delle dipendenze per evitare violazioni dei vincoli di integrita.
        self.stdout.write("Pulizia dati esistenti...")
        RispostaUtenteQuiz.objects.all().delete()
        Partecipazione.objects.all().delete()
        Risposta.objects.all().delete()
        Domanda.objects.all().delete()
        Quiz.objects.all().delete()
        Utente.objects.all().delete()

        # Fase 2: creazione degli utenti, con username univoco derivato da nome e cognome.
        self.stdout.write("Creazione utenti...")
        utenti = []
        used_usernames = set()
        for i in range(N_UTENTI):
            nome = nomi[i % len(nomi)]
            cognome = cognomi[i % len(cognomi)]
            base = (nome[0] + cognome).lower().replace(" ", "")[:12]
            username = base
            suffix = 1
            while username in used_usernames:
                username = f"{base}{suffix}"
                suffix += 1
            used_usernames.add(username)
            utente = Utente.objects.create(
                nome_utente=username,
                nome=nome,
                cognome=cognome,
                email=f"{username}@email.com",
            )
            utenti.append(utente)

        # Fase 3: creazione dei quiz, ciascuno assegnato a un creatore casuale
        # e con un periodo di validita generato casualmente.
        self.stdout.write("Creazione quiz...")
        quiz_objs = []
        for i in range(1, N_QUIZ + 1):
            creatore = random.choice(utenti)
            tema = random.choice(temi_quiz)
            d_inizio = data_casuale(date(2023, 1, 1), date(2025, 1, 1))
            d_fine = d_inizio + timedelta(days=random.randint(30, 365))
            quiz = Quiz.objects.create(
                creatore=creatore,
                titolo=f"Quiz {tema} #{i}",
                data_inizio=d_inizio,
                data_fine=d_fine,
            )
            quiz_objs.append(quiz)

        # Fase 4: per ogni quiz genera un numero variabile di domande, assegnando
        # i testi a rotazione da un pool mescolato per varieta tra i quiz.
        self.stdout.write("Creazione domande e risposte...")
        domande_per_quiz = {}
        testi_pool = testi_domande.copy()
        random.shuffle(testi_pool)
        testo_idx = 0

        for quiz in quiz_objs:
            n_dom = random.randint(MIN_DOMANDE, MAX_DOMANDE)
            domande_per_quiz[quiz.id] = []

            for num_dom in range(1, n_dom + 1):
                testo_dom = testi_pool[testo_idx % len(testi_pool)]
                testo_idx += 1
                domanda = Domanda.objects.create(
                    quiz=quiz,
                    numero=num_dom,
                    testo=testo_dom,
                )

                # Determina quante risposte corrette e sbagliate generare per la
                # domanda e ne mescola l'ordine di presentazione.
                n_risp = random.randint(MIN_RISPOSTE, MAX_RISPOSTE)
                n_corrette = random.randint(1, max(1, n_risp - 1))
                tipi = ["Corretta"] * n_corrette + ["Sbagliata"] * (n_risp - n_corrette)
                random.shuffle(tipi)

                testi_corretti = scegli_risposte(testo_dom, "Corretta", n_corrette)
                testi_sbagliati = scegli_risposte(testo_dom, "Sbagliata", n_risp - n_corrette)

                risposte_obj = []
                for num_risp, tipo in enumerate(tipi, start=1):
                    if tipo == "Corretta":
                        risposta = Risposta.objects.create(
                            domanda=domanda,
                            numero=num_risp,
                            testo=testi_corretti.pop(),
                            tipo="Corretta",
                            punteggio=Decimal(str(round(random.uniform(0.5, 2.0), 1))),
                        )
                    else:
                        risposta = Risposta.objects.create(
                            domanda=domanda,
                            numero=num_risp,
                            testo=testi_sbagliati.pop(),
                            tipo="Sbagliata",
                            punteggio=None,
                        )
                    risposte_obj.append(risposta)

                domande_per_quiz[quiz.id].append((domanda, risposte_obj))

        # Fase 5: per ogni utente crea un numero variabile di partecipazioni a quiz
        # scelti casualmente, generando anche una risposta data per ogni domanda del quiz.
        self.stdout.write("Creazione partecipazioni e risposte utente...")
        for utente in utenti:
            n_part = random.randint(MIN_PART, MAX_PART)
            quiz_scelti = random.sample(quiz_objs, min(n_part, len(quiz_objs)))

            for quiz in quiz_scelti:
                data_part = data_casuale(quiz.data_inizio, quiz.data_fine)
                partecipazione = Partecipazione.objects.create(
                    utente=utente,
                    quiz=quiz,
                    data=data_part,
                )

                for domanda, risposte_obj in domande_per_quiz[quiz.id]:
                    risposta_scelta = random.choice(risposte_obj)
                    RispostaUtenteQuiz.objects.create(
                        partecipazione=partecipazione,
                        domanda=domanda,
                        risposta=risposta_scelta,
                    )

        self.stdout.write(self.style.SUCCESS("Seed completato."))
        self.stdout.write(f"  Utenti:         {Utente.objects.count()}")
        self.stdout.write(f"  Quiz:           {Quiz.objects.count()}")
        self.stdout.write(f"  Domande:        {Domanda.objects.count()}")
        self.stdout.write(f"  Risposte:       {Risposta.objects.count()}")
        self.stdout.write(f"  Partecipazioni: {Partecipazione.objects.count()}")
        self.stdout.write(f"  Risposte date:  {RispostaUtenteQuiz.objects.count()}")