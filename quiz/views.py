# Quiz Online - Progetto #2, gruppo BP Solutions
# Contiene le view dell'applicazione: pagina home, ricerche con filtri
# per utenti/quiz/partecipazioni e il CRUD sulla tabella Partecipazione.
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Min, Max, Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Utente, Quiz, Domanda, Risposta, Partecipazione, RispostaUtenteQuiz


RIGHE_PER_PAGINA = 25


def leggi_intero(request, nome):
    """Legge un parametro GET intero, ignorandolo se non valido."""
    valore = request.GET.get(nome, "").strip()
    if not valore:
        return "", None
    try:
        return valore, int(valore)
    except ValueError:
        return valore, None


def leggi_decimale(request, nome):
    """Legge un parametro GET decimale, ignorandolo se non valido."""
    valore = request.GET.get(nome, "").strip().replace(",", ".")
    if not valore:
        return "", None
    try:
        return valore, Decimal(valore)
    except InvalidOperation:
        return valore, None


def crea_querystring(request, aggiornamenti=None, rimuovi=None):
    """Costruisce una querystring mantenendo i parametri GET correnti."""
    query = request.GET.copy()
    for chiave in rimuovi or []:
        query.pop(chiave, None)
    for chiave, valore in (aggiornamenti or {}).items():
        if valore in (None, ""):
            query.pop(chiave, None)
        else:
            query[chiave] = str(valore)
    return query.urlencode()


def applica_ordinamento(queryset, request, ordinamenti, ordinamento_default):
    """Applica un ordinamento GET solo se incluso nella whitelist della vista."""
    ordinamento = request.GET.get("sort", ordinamento_default)
    if ordinamento not in ordinamenti:
        ordinamento = ordinamento_default
    return queryset.order_by(*ordinamenti[ordinamento]), ordinamento


def link_ordinamento(request, ordinamento_corrente, campi):
    """Prepara i link di ordinamento preservando filtri e rimuovendo la pagina."""
    links = {}
    for chiave, campo in campi.items():
        inverso = f"-{campo}"
        prossimo = inverso if ordinamento_corrente == campo else campo
        indicatore = "↕"
        if ordinamento_corrente == campo:
            indicatore = "↑"
        elif ordinamento_corrente == inverso:
            indicatore = "↓"
        links[chiave] = {
            "url": crea_querystring(
                request,
                aggiornamenti={"sort": prossimo},
                rimuovi=["page"],
            ),
            "attivo": ordinamento_corrente in (campo, inverso),
            "indicatore": indicatore,
        }
    return links


def pagina_queryset(request, queryset, per_page=RIGHE_PER_PAGINA):
    """Restituisce la pagina richiesta usando il Paginator di Django."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def numeri_paginazione(page_obj, raggio=2):
    """Restituisce una sequenza compatta di pagine da mostrare nel template."""
    totale = page_obj.paginator.num_pages
    corrente = page_obj.number
    numeri = {1, totale}
    for numero in range(corrente - raggio, corrente + raggio + 1):
        if 1 <= numero <= totale:
            numeri.add(numero)

    risultato = []
    precedente = None
    for numero in sorted(numeri):
        if precedente is not None and numero - precedente > 1:
            risultato.append("...")
        risultato.append(numero)
        precedente = numero
    return risultato


def aggiungi_errori_validazione(errori, eccezione):
    """Converte una ValidationError di Django in messaggi leggibili per l'utente."""
    if hasattr(eccezione, "message_dict"):
        for messaggi in eccezione.message_dict.values():
            errori.extend(messaggi)
    else:
        errori.extend(eccezione.messages)


def url_ritorno_sicuro(request, default_name):
    """Restituisce un URL di ritorno locale, ignorando valori next/back_url non sicuri."""
    candidato = (
        request.POST.get("next")
        or request.POST.get("back_url")
        or request.GET.get("next")
        or request.GET.get("back_url")
        or ""
    ).strip()
    if candidato and url_has_allowed_host_and_scheme(
        candidato,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidato
    return reverse(default_name)


def home(request):
    """Mostra la pagina iniziale con i conteggi complessivi di utenti, quiz, domande e partecipazioni."""
    contesto = {
        "active": "home",
        "n_utenti": Utente.objects.count(),
        "n_quiz": Quiz.objects.count(),
        "n_domande": Domanda.objects.count(),
        "n_partecipazioni": Partecipazione.objects.count(),
    }
    return render(request, "quiz/home.html", contesto)


def ricerca_utenti(request):
    """Elenca gli utenti applicando in AND i filtri opzionali ricevuti via querystring GET."""
    utenti = Utente.objects.annotate(
        n_quiz_creati=Count("quiz_creati", distinct=True),
        n_partecipazioni=Count("partecipazioni", distinct=True),
    )

    nome_utente = request.GET.get("nome_utente", "").strip()
    nome = request.GET.get("nome", "").strip()
    cognome = request.GET.get("cognome", "").strip()
    email = request.GET.get("email", "").strip()
    quiz_creati_min, quiz_creati_min_valore = leggi_intero(request, "quiz_creati_min")
    quiz_creati_max, quiz_creati_max_valore = leggi_intero(request, "quiz_creati_max")
    partecipazioni_min, partecipazioni_min_valore = leggi_intero(request, "partecipazioni_min")
    partecipazioni_max, partecipazioni_max_valore = leggi_intero(request, "partecipazioni_max")

    # Applica ogni filtro solo se l'utente ha effettivamente valorizzato il campo.
    if nome_utente:
        utenti = utenti.filter(nome_utente__icontains=nome_utente)
    if nome:
        utenti = utenti.filter(nome__icontains=nome)
    if cognome:
        utenti = utenti.filter(cognome__icontains=cognome)
    if email:
        utenti = utenti.filter(email__icontains=email)
    if quiz_creati_min_valore is not None:
        utenti = utenti.filter(n_quiz_creati__gte=quiz_creati_min_valore)
    if quiz_creati_max_valore is not None:
        utenti = utenti.filter(n_quiz_creati__lte=quiz_creati_max_valore)
    if partecipazioni_min_valore is not None:
        utenti = utenti.filter(n_partecipazioni__gte=partecipazioni_min_valore)
    if partecipazioni_max_valore is not None:
        utenti = utenti.filter(n_partecipazioni__lte=partecipazioni_max_valore)

    ordinamenti = {
        "nome_utente": ("nome_utente", "id"),
        "-nome_utente": ("-nome_utente", "id"),
        "nome": ("nome", "cognome", "id"),
        "-nome": ("-nome", "cognome", "id"),
        "cognome": ("cognome", "nome", "id"),
        "-cognome": ("-cognome", "nome", "id"),
        "email": ("email", "id"),
        "-email": ("-email", "id"),
        "quiz_creati": ("n_quiz_creati", "nome_utente", "id"),
        "-quiz_creati": ("-n_quiz_creati", "nome_utente", "id"),
        "partecipazioni": ("n_partecipazioni", "nome_utente", "id"),
        "-partecipazioni": ("-n_partecipazioni", "nome_utente", "id"),
    }
    utenti, ordinamento = applica_ordinamento(
        utenti,
        request,
        ordinamenti,
        "nome_utente",
    )
    pagina_utenti = pagina_queryset(request, utenti)

    contesto = {
        "active": "utenti",
        "utenti": pagina_utenti,
        "page_obj": pagina_utenti,
        "page_numbers": numeri_paginazione(pagina_utenti),
        "page_querystring": crea_querystring(request, rimuovi=["page"]),
        "sort": ordinamento,
        "sort_links": link_ordinamento(
            request,
            ordinamento,
            {
                "nome_utente": "nome_utente",
                "nome": "nome",
                "cognome": "cognome",
                "email": "email",
                "quiz_creati": "quiz_creati",
                "partecipazioni": "partecipazioni",
            },
        ),
        "filtri": {
            "nome_utente": nome_utente,
            "nome": nome,
            "cognome": cognome,
            "email": email,
            "quiz_creati_min": quiz_creati_min,
            "quiz_creati_max": quiz_creati_max,
            "partecipazioni_min": partecipazioni_min,
            "partecipazioni_max": partecipazioni_max,
        },
    }
    return render(request, "quiz/ricerca_utenti.html", contesto)


def dettaglio_utente(request, utente_id):
    """Mostra la scheda di un utente con dati anagrafici e attivita principali."""
    utente = get_object_or_404(Utente, pk=utente_id)
    quiz_creati = (
        utente.quiz_creati
        .annotate(
            n_domande=Count("domande", distinct=True),
            n_partecipazioni=Count("partecipazioni", distinct=True),
        )
        .order_by("titolo")[:10]
    )
    partecipazioni = (
        utente.partecipazioni
        .select_related("quiz")
        .order_by("-data", "quiz__titolo")[:10]
    )

    contesto = {
        "active": "utenti",
        "utente": utente,
        "quiz_creati": quiz_creati,
        "partecipazioni": partecipazioni,
        "n_quiz_creati": utente.quiz_creati.count(),
        "n_partecipazioni": utente.partecipazioni.count(),
        "back_url": url_ritorno_sicuro(request, "ricerca_utenti"),
    }
    return render(request, "quiz/dettaglio_utente.html", contesto)


def ricerca_quiz(request):
    """Elenca i quiz applicando in AND i filtri opzionali su titolo, creatore e intervallo date."""
    elenco_quiz = Quiz.objects.select_related("creatore").annotate(
        n_domande=Count("domande", distinct=True),
        n_partecipazioni=Count("partecipazioni", distinct=True),
        punteggio_medio=Avg("partecipazioni__risposte_date__risposta__punteggio"),
        punteggio_minimo=Min("partecipazioni__risposte_date__risposta__punteggio"),
        punteggio_massimo=Max("partecipazioni__risposte_date__risposta__punteggio"),
    )

    titolo = request.GET.get("titolo", "").strip()
    autore = request.GET.get("autore", request.GET.get("creatore", "")).strip()
    data_da = request.GET.get("data_da", "").strip()
    data_a = request.GET.get("data_a", "").strip()
    domande_min, domande_min_valore = leggi_intero(request, "domande_min")
    domande_max, domande_max_valore = leggi_intero(request, "domande_max")
    partecipazioni_min, partecipazioni_min_valore = leggi_intero(request, "partecipazioni_min")
    partecipazioni_max, partecipazioni_max_valore = leggi_intero(request, "partecipazioni_max")
    punteggio_medio_min, punteggio_medio_min_valore = leggi_decimale(request, "punteggio_medio_min")
    punteggio_medio_max, punteggio_medio_max_valore = leggi_decimale(request, "punteggio_medio_max")
    punteggio_minimo_min, punteggio_minimo_min_valore = leggi_decimale(request, "punteggio_minimo_min")
    punteggio_minimo_max, punteggio_minimo_max_valore = leggi_decimale(request, "punteggio_minimo_max")
    punteggio_massimo_min, punteggio_massimo_min_valore = leggi_decimale(request, "punteggio_massimo_min")
    punteggio_massimo_max, punteggio_massimo_max_valore = leggi_decimale(request, "punteggio_massimo_max")

    # Applica ogni filtro solo se l'utente ha effettivamente valorizzato il campo.
    if titolo:
        elenco_quiz = elenco_quiz.filter(titolo__icontains=titolo)
    if autore:
        elenco_quiz = elenco_quiz.filter(creatore__nome_utente__icontains=autore)
    if data_da:
        elenco_quiz = elenco_quiz.filter(data_inizio__gte=data_da)
    if data_a:
        elenco_quiz = elenco_quiz.filter(data_fine__lte=data_a)
    if domande_min_valore is not None:
        elenco_quiz = elenco_quiz.filter(n_domande__gte=domande_min_valore)
    if domande_max_valore is not None:
        elenco_quiz = elenco_quiz.filter(n_domande__lte=domande_max_valore)
    if partecipazioni_min_valore is not None:
        elenco_quiz = elenco_quiz.filter(n_partecipazioni__gte=partecipazioni_min_valore)
    if partecipazioni_max_valore is not None:
        elenco_quiz = elenco_quiz.filter(n_partecipazioni__lte=partecipazioni_max_valore)
    if punteggio_medio_min_valore is not None:
        elenco_quiz = elenco_quiz.filter(punteggio_medio__gte=punteggio_medio_min_valore)
    if punteggio_medio_max_valore is not None:
        elenco_quiz = elenco_quiz.filter(punteggio_medio__lte=punteggio_medio_max_valore)
    if punteggio_minimo_min_valore is not None:
        elenco_quiz = elenco_quiz.filter(punteggio_minimo__gte=punteggio_minimo_min_valore)
    if punteggio_minimo_max_valore is not None:
        elenco_quiz = elenco_quiz.filter(punteggio_minimo__lte=punteggio_minimo_max_valore)
    if punteggio_massimo_min_valore is not None:
        elenco_quiz = elenco_quiz.filter(punteggio_massimo__gte=punteggio_massimo_min_valore)
    if punteggio_massimo_max_valore is not None:
        elenco_quiz = elenco_quiz.filter(punteggio_massimo__lte=punteggio_massimo_max_valore)

    ordinamenti = {
        "titolo": ("titolo", "id"),
        "-titolo": ("-titolo", "id"),
        "autore": ("creatore__nome_utente", "titolo", "id"),
        "-autore": ("-creatore__nome_utente", "titolo", "id"),
        "data_inizio": ("data_inizio", "titolo", "id"),
        "-data_inizio": ("-data_inizio", "titolo", "id"),
        "data_fine": ("data_fine", "titolo", "id"),
        "-data_fine": ("-data_fine", "titolo", "id"),
        "domande": ("n_domande", "titolo", "id"),
        "-domande": ("-n_domande", "titolo", "id"),
        "partecipazioni": ("n_partecipazioni", "titolo", "id"),
        "-partecipazioni": ("-n_partecipazioni", "titolo", "id"),
        "punteggio_medio": ("punteggio_medio", "titolo", "id"),
        "-punteggio_medio": ("-punteggio_medio", "titolo", "id"),
        "punteggio_minimo": ("punteggio_minimo", "titolo", "id"),
        "-punteggio_minimo": ("-punteggio_minimo", "titolo", "id"),
        "punteggio_massimo": ("punteggio_massimo", "titolo", "id"),
        "-punteggio_massimo": ("-punteggio_massimo", "titolo", "id"),
    }
    elenco_quiz, ordinamento = applica_ordinamento(
        elenco_quiz,
        request,
        ordinamenti,
        "titolo",
    )
    pagina_quiz = pagina_queryset(request, elenco_quiz)

    contesto = {
        "active": "quiz",
        "elenco_quiz": pagina_quiz,
        "page_obj": pagina_quiz,
        "page_numbers": numeri_paginazione(pagina_quiz),
        "page_querystring": crea_querystring(request, rimuovi=["page"]),
        "sort": ordinamento,
        "sort_links": link_ordinamento(
            request,
            ordinamento,
            {
                "titolo": "titolo",
                "autore": "autore",
                "data_inizio": "data_inizio",
                "data_fine": "data_fine",
                "domande": "domande",
                "partecipazioni": "partecipazioni",
                "punteggio_medio": "punteggio_medio",
                "punteggio_minimo": "punteggio_minimo",
                "punteggio_massimo": "punteggio_massimo",
            },
        ),
        "filtri": {
            "titolo": titolo,
            "autore": autore,
            "data_da": data_da,
            "data_a": data_a,
            "domande_min": domande_min,
            "domande_max": domande_max,
            "partecipazioni_min": partecipazioni_min,
            "partecipazioni_max": partecipazioni_max,
            "punteggio_medio_min": punteggio_medio_min,
            "punteggio_medio_max": punteggio_medio_max,
            "punteggio_minimo_min": punteggio_minimo_min,
            "punteggio_minimo_max": punteggio_minimo_max,
            "punteggio_massimo_min": punteggio_massimo_min,
            "punteggio_massimo_max": punteggio_massimo_max,
        },
    }
    return render(request, "quiz/ricerca_quiz.html", contesto)


def dettaglio_quiz(request, quiz_id):
    """Mostra i dettagli di un quiz con le sue domande, le risposte correlate e il numero di partecipazioni."""
    quiz = get_object_or_404(
        Quiz.objects.select_related("creatore"), pk=quiz_id
    )
    domande = quiz.domande.prefetch_related(
        Prefetch("risposte", queryset=Risposta.objects.order_by("numero"))
    ).order_by("numero", "id")
    punteggi = quiz.partecipazioni.aggregate(
        punteggio_medio=Avg("risposte_date__risposta__punteggio"),
        punteggio_minimo=Min("risposte_date__risposta__punteggio"),
        punteggio_massimo=Max("risposte_date__risposta__punteggio"),
    )

    contesto = {
        "active": "quiz",
        "quiz": quiz,
        "domande": domande,
        "n_domande": domande.count(),
        "n_partecipazioni": quiz.partecipazioni.count(),
        "punteggio_medio": punteggi["punteggio_medio"],
        "punteggio_minimo": punteggi["punteggio_minimo"],
        "punteggio_massimo": punteggi["punteggio_massimo"],
        "back_url": url_ritorno_sicuro(request, "ricerca_quiz"),
    }
    return render(request, "quiz/dettaglio_quiz.html", contesto)


def ricerca_partecipazioni(request):
    """Elenca le partecipazioni applicando in AND i filtri opzionali su utente, quiz e intervallo date."""
    partecipazioni = Partecipazione.objects.select_related(
        "utente", "quiz"
    )

    utente = request.GET.get("utente", "").strip()
    titolo_quiz = request.GET.get("quiz", "").strip()
    data_da = request.GET.get("data_da", "").strip()
    data_a = request.GET.get("data_a", "").strip()

    # Applica ogni filtro solo se l'utente ha effettivamente valorizzato il campo.
    if utente:
        partecipazioni = partecipazioni.filter(
            utente__nome_utente__icontains=utente
        )
    if titolo_quiz:
        partecipazioni = partecipazioni.filter(
            quiz__titolo__icontains=titolo_quiz
        )
    if data_da:
        partecipazioni = partecipazioni.filter(data__gte=data_da)
    if data_a:
        partecipazioni = partecipazioni.filter(data__lte=data_a)

    ordinamenti = {
        "utente": ("utente__nome_utente", "-data", "id"),
        "-utente": ("-utente__nome_utente", "-data", "id"),
        "quiz": ("quiz__titolo", "-data", "id"),
        "-quiz": ("-quiz__titolo", "-data", "id"),
        "data": ("data", "id"),
        "-data": ("-data", "id"),
    }
    partecipazioni, ordinamento = applica_ordinamento(
        partecipazioni,
        request,
        ordinamenti,
        "-data",
    )
    pagina_partecipazioni = pagina_queryset(request, partecipazioni)

    contesto = {
        "active": "partecipazioni",
        "partecipazioni": pagina_partecipazioni,
        "page_obj": pagina_partecipazioni,
        "page_numbers": numeri_paginazione(pagina_partecipazioni),
        "page_querystring": crea_querystring(request, rimuovi=["page"]),
        "sort": ordinamento,
        "sort_links": link_ordinamento(
            request,
            ordinamento,
            {
                "utente": "utente",
                "quiz": "quiz",
                "data": "data",
            },
        ),
        "filtri": {
            "utente": utente,
            "quiz": titolo_quiz,
            "data_da": data_da,
            "data_a": data_a,
        },
    }
    return render(request, "quiz/ricerca_partecipazioni.html", contesto)


def dettaglio_partecipazione(request, partecipazione_id):
    """Mostra la scheda di una partecipazione con riepilogo e risposte date."""
    partecipazione = get_object_or_404(
        Partecipazione.objects.select_related("utente", "quiz").prefetch_related(
            Prefetch(
                "risposte_date",
                queryset=(
                    RispostaUtenteQuiz.objects
                    .select_related("domanda", "risposta")
                    .order_by("domanda__numero")
                ),
            )
        ),
        pk=partecipazione_id,
    )
    risposte_date = partecipazione.risposte_date.all()

    contesto = {
        "active": "partecipazioni",
        "partecipazione": partecipazione,
        "risposte_date": risposte_date,
        "back_url": url_ritorno_sicuro(request, "ricerca_partecipazioni"),
    }
    return render(request, "quiz/dettaglio_partecipazione.html", contesto)


def valida_partecipazione(utente_id, quiz_id, data_str):
    """Valida i dati grezzi di una partecipazione (utente, quiz, data) restituendo
    la lista di errori insieme agli oggetti risolti, cosi da poter essere riusata
    sia in creazione che in modifica."""
    errori = []
    utente = None
    quiz = None
    data_part = None

    # Verifica che l'utente sia stato selezionato e che esista realmente.
    if not utente_id:
        errori.append("Selezionare un utente.")
    else:
        utente = Utente.objects.filter(pk=utente_id).first()
        if utente is None:
            errori.append("L'utente selezionato non esiste.")

    # Verifica che il quiz sia stato selezionato e che esista realmente.
    if not quiz_id:
        errori.append("Selezionare un quiz.")
    else:
        quiz = Quiz.objects.filter(pk=quiz_id).first()
        if quiz is None:
            errori.append("Il quiz selezionato non esiste.")

    # Verifica che la data sia presente e in un formato ISO valido.
    if not data_str:
        errori.append("Inserire la data di partecipazione.")
    else:
        try:
            data_part = date.fromisoformat(data_str)
        except ValueError:
            errori.append("La data inserita non è valida.")
        else:
            if data_part > timezone.localdate():
                errori.append("La data di partecipazione non può essere futura.")

    # Verifica di coerenza incrociata: la data deve rientrare nel periodo di validità del quiz.
    if quiz is not None and data_part is not None:
        if data_part < quiz.data_inizio or data_part > quiz.data_fine:
            errori.append(
                f"La data deve essere compresa nel periodo di validità del quiz "
                f"({quiz.data_inizio.strftime('%d/%m/%Y')} - {quiz.data_fine.strftime('%d/%m/%Y')})."
            )

    return errori, utente, quiz, data_part


def crea_partecipazione(request):
    """Gestisce la creazione di una nuova partecipazione: mostra il form in GET
    e valida/salva i dati in POST, evitando duplicati utente-quiz-data."""
    utente_id = ""
    quiz_id = ""
    data_str = ""
    back_url = url_ritorno_sicuro(request, "ricerca_partecipazioni")

    if request.method == "POST":
        utente_id = request.POST.get("utente", "").strip()
        quiz_id = request.POST.get("quiz", "").strip()
        data_str = request.POST.get("data", "").strip()

        errori, utente, quiz, data_part = valida_partecipazione(
            utente_id, quiz_id, data_str
        )

        # Oltre alla validazione dei campi, verifica che non esista gia
        # una partecipazione identica (stesso utente, quiz e data).
        if not errori:
            duplicata = Partecipazione.objects.filter(
                utente=utente, quiz=quiz, data=data_part
            ).exists()
            if duplicata:
                errori.append(
                    "Esiste già una partecipazione di questo utente a questo quiz in questa data."
                )

        if not errori:
            partecipazione = Partecipazione(utente=utente, quiz=quiz, data=data_part)
            try:
                partecipazione.save()
            except ValidationError as eccezione:
                aggiungi_errori_validazione(errori, eccezione)
            else:
                messages.success(request, "Partecipazione creata correttamente.")
                return redirect(back_url)

        for errore in errori:
            messages.error(request, errore)

    contesto = {
        "active": "partecipazioni",
        "titolo_pagina": "Nuova partecipazione",
        "utenti": Utente.objects.order_by("nome_utente"),
        "elenco_quiz": Quiz.objects.order_by("titolo"),
        "valori": {"utente": utente_id, "quiz": quiz_id, "data": data_str},
        "url_annulla": "ricerca_partecipazioni",
        "back_url": back_url,
    }
    return render(request, "quiz/form_partecipazione.html", contesto)


def modifica_partecipazione(request, partecipazione_id):
    """Gestisce la modifica di una partecipazione esistente: precompila il form in GET
    e valida/aggiorna i dati in POST, escludendo il record corrente dal controllo duplicati."""
    partecipazione = get_object_or_404(
        Partecipazione.objects.select_related("utente", "quiz"),
        pk=partecipazione_id,
    )
    back_url = url_ritorno_sicuro(request, "ricerca_partecipazioni")

    if request.method == "POST":
        utente_id = request.POST.get("utente", "").strip()
        quiz_id = request.POST.get("quiz", "").strip()
        data_str = request.POST.get("data", "").strip()

        errori, utente, quiz, data_part = valida_partecipazione(
            utente_id, quiz_id, data_str
        )

        # Il controllo duplicati esclude il record che si sta modificando,
        # altrimenti la partecipazione risulterebbe sempre in conflitto con se stessa.
        if not errori:
            duplicata = (
                Partecipazione.objects.filter(
                    utente=utente, quiz=quiz, data=data_part
                )
                .exclude(pk=partecipazione.pk)
                .exists()
            )
            if duplicata:
                errori.append(
                    "Esiste già una partecipazione di questo utente a questo quiz in questa data."
                )

        if not errori:
            partecipazione.utente = utente
            partecipazione.quiz = quiz
            partecipazione.data = data_part
            try:
                partecipazione.save()
            except ValidationError as eccezione:
                aggiungi_errori_validazione(errori, eccezione)
            else:
                messages.success(request, "Partecipazione modificata correttamente.")
                return redirect(back_url)

        for errore in errori:
            messages.error(request, errore)

        valori = {"utente": utente_id, "quiz": quiz_id, "data": data_str}
    else:
        # Richiesta GET: precompila il form con i valori attuali della partecipazione.
        valori = {
            "utente": str(partecipazione.utente_id),
            "quiz": str(partecipazione.quiz_id),
            "data": partecipazione.data.isoformat(),
        }

    contesto = {
        "active": "partecipazioni",
        "titolo_pagina": "Modifica partecipazione",
        "utenti": Utente.objects.order_by("nome_utente"),
        "elenco_quiz": Quiz.objects.order_by("titolo"),
        "valori": valori,
        "url_annulla": "ricerca_partecipazioni",
        "back_url": back_url,
    }
    return render(request, "quiz/form_partecipazione.html", contesto)


def elimina_partecipazione(request, partecipazione_id):
    """Gestisce l'eliminazione di una partecipazione: mostra una conferma in GET
    ed esegue la cancellazione effettiva solo in POST."""
    partecipazione = get_object_or_404(
        Partecipazione.objects.select_related("utente", "quiz"),
        pk=partecipazione_id,
    )
    back_url = url_ritorno_sicuro(request, "ricerca_partecipazioni")

    if request.method == "POST":
        partecipazione.delete()
        messages.success(request, "Partecipazione eliminata correttamente.")
        return redirect(back_url)

    contesto = {
        "active": "partecipazioni",
        "partecipazione": partecipazione,
        "back_url": back_url,
    }
    return render(request, "quiz/elimina_partecipazione.html", contesto)
