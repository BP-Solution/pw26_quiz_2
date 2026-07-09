# Quiz Online - Progetto #2, gruppo BP Solutions
# Contiene le view dell'applicazione: pagina home, ricerche con filtri
# per utenti/quiz/partecipazioni e il CRUD sulla tabella Partecipazione.
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, DecimalField, Min, Max, OuterRef, Prefetch, Subquery, Sum, Value
from django.db.models.functions import Coalesce
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


def espressione_punteggio_totale_partecipazione(riferimento="pk"):
    """Espressione che calcola il punteggio totale di una partecipazione, cioè la somma
    dei punteggi delle risposte date (le risposte senza punteggio valgono 0). Va usata
    dentro un queryset di Partecipazione, correlato tramite OuterRef(riferimento)."""
    return Coalesce(
        Subquery(
            RispostaUtenteQuiz.objects
            .filter(partecipazione_id=OuterRef(riferimento))
            .values("partecipazione_id")
            .annotate(totale=Sum("risposta__punteggio"))
            .values("totale"),
            output_field=DecimalField(max_digits=6, decimal_places=1),
        ),
        Value(Decimal("0")),
    )


def statistiche_punteggio_quiz(riferimento_quiz="pk"):
    """Subquery di media/minimo/massimo calcolate sul punteggio totale di ciascuna
    partecipazione al quiz (non sulle singole risposte), evitando cosi di sottostimare
    il punteggio dei quiz con molte domande. Pensata per essere usata come annotazione
    su un queryset di Quiz, correlato tramite OuterRef(riferimento_quiz)."""
    punteggi_partecipazioni = (
        Partecipazione.objects
        .filter(quiz=OuterRef(riferimento_quiz))
        .annotate(punteggio_totale=espressione_punteggio_totale_partecipazione())
        .values("quiz_id")
        .annotate(
            media=Avg("punteggio_totale"),
            minimo=Min("punteggio_totale"),
            massimo=Max("punteggio_totale"),
        )
    )
    output_field = DecimalField(max_digits=8, decimal_places=2)
    return {
        "punteggio_medio": Subquery(punteggi_partecipazioni.values("media"), output_field=output_field),
        "punteggio_minimo": Subquery(punteggi_partecipazioni.values("minimo"), output_field=output_field),
        "punteggio_massimo": Subquery(punteggi_partecipazioni.values("massimo"), output_field=output_field),
    }


def ricerca_quiz(request):
    """Elenca i quiz applicando in AND i filtri opzionali su titolo, creatore e intervallo date."""
    elenco_quiz = Quiz.objects.select_related("creatore").annotate(
        n_domande=Count("domande", distinct=True),
        n_partecipazioni=Count("partecipazioni", distinct=True),
        **statistiche_punteggio_quiz(),
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
    # Media/minimo/massimo vanno calcolati sul punteggio totale di ciascuna
    # partecipazione (somma dei punteggi delle sue risposte), non sulle singole risposte.
    punteggi = quiz.partecipazioni.annotate(
        punteggio_totale=espressione_punteggio_totale_partecipazione()
    ).aggregate(
        punteggio_medio=Avg("punteggio_totale"),
        punteggio_minimo=Min("punteggio_totale"),
        punteggio_massimo=Max("punteggio_totale"),
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
    # n_risposte serve solo a distinguere le partecipazioni senza risposte registrate
    # (mostrate con "—") da quelle il cui punteggio totale e effettivamente 0.
    partecipazioni = Partecipazione.objects.select_related("utente", "quiz").annotate(
        n_risposte=Count("risposte_date", distinct=True),
        punteggio_totale=Coalesce(
            Sum("risposte_date__risposta__punteggio"), Value(Decimal("0"))
        ),
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
        "punteggio": ("punteggio_totale", "-data", "id"),
        "-punteggio": ("-punteggio_totale", "-data", "id"),
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
                "punteggio": "punteggio",
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
    # Punteggio totale calcolato in Python sulle risposte gia recuperate dal prefetch,
    # senza eseguire query aggiuntive (le risposte senza punteggio valgono 0).
    punteggio_totale = sum(
        (risposta_data.risposta.punteggio or Decimal("0")) for risposta_data in risposte_date
    )

    contesto = {
        "active": "partecipazioni",
        "partecipazione": partecipazione,
        "risposte_date": risposte_date,
        "punteggio_totale": punteggio_totale,
        "back_url": url_ritorno_sicuro(request, "ricerca_partecipazioni"),
    }
    return render(request, "quiz/dettaglio_partecipazione.html", contesto)


def valida_data_partecipazione(data_str, quiz):
    """Valida la data di una partecipazione: presenza, formato ISO, non futura e
    (se il quiz e noto) compresa nel suo periodo di validità. Usata sia in creazione
    sia in modifica, dove utente e quiz non sono piu modificabili."""
    errori = []
    data_part = None

    if not data_str:
        errori.append("Inserire la data di partecipazione.")
        return errori, None

    try:
        data_part = date.fromisoformat(data_str)
    except ValueError:
        errori.append("La data inserita non è valida.")
        return errori, None

    if data_part > timezone.localdate():
        errori.append("La data di partecipazione non può essere futura.")

    if quiz is not None and (data_part < quiz.data_inizio or data_part > quiz.data_fine):
        errori.append(
            f"La data deve essere compresa nel periodo di validità del quiz "
            f"({quiz.data_inizio.strftime('%d/%m/%Y')} - {quiz.data_fine.strftime('%d/%m/%Y')})."
        )

    return errori, data_part


def valida_partecipazione(nome_utente, titolo_quiz, data_str):
    """Valida i dati grezzi di una nuova partecipazione, risolvendo utente e quiz a
    partire dal testo digitato nei campi con autocompletamento (username e titolo)
    invece che da un id di select, e restituisce la lista di errori insieme agli
    oggetti risolti."""
    errori = []
    utente = None
    quiz = None

    # Risolve lo username in un utente esistente: nome_utente e univoco nel modello,
    # quindi l'unica alternativa a una corrispondenza esatta e l'assenza di risultati.
    if not nome_utente:
        errori.append("Selezionare un utente.")
    else:
        utente = Utente.objects.filter(nome_utente=nome_utente).first()
        if utente is None:
            errori.append(
                "L'utente indicato non esiste: digitare uno username presente nell'elenco suggerito."
            )

    # Risolve il titolo in un quiz esistente. Il titolo non e vincolato a essere
    # univoco, quindi va gestito anche il caso di piu quiz con lo stesso titolo.
    if not titolo_quiz:
        errori.append("Selezionare un quiz.")
    else:
        corrispondenze = list(
            Quiz.objects.filter(titolo=titolo_quiz)
            .annotate(n_domande=Count("domande"))[:2]
        )
        if not corrispondenze:
            errori.append(
                "Il quiz indicato non esiste: digitare un titolo presente nell'elenco suggerito."
            )
        elif len(corrispondenze) > 1:
            errori.append(
                "Il titolo indicato corrisponde a più quiz: sceglierne uno dall'elenco suggerito."
            )
        elif corrispondenze[0].n_domande == 0:
            errori.append("Il quiz selezionato non ha domande e non può ricevere partecipazioni.")
        else:
            quiz = corrispondenze[0]

    errori_data, data_part = valida_data_partecipazione(data_str, quiz)
    errori.extend(errori_data)

    return errori, utente, quiz, data_part


def costruisci_domande_risposta(quiz):
    """Prepara, per ciascuna domanda del quiz, l'elenco delle opzioni di risposta da
    proporre nella maschera di partecipazione (senza rivelare quale sia corretta).
    Ogni opzione porta con se un flag "selezionata", usato per ripresentare le
    scelte gia fatte quando il form viene ripetuto a causa di un errore."""
    domande = quiz.domande.prefetch_related(
        Prefetch("risposte", queryset=Risposta.objects.order_by("numero"))
    ).order_by("numero", "id")

    domande_risposta = []
    for domanda in domande:
        opzioni = [
            {"risposta": risposta, "selezionata": False}
            for risposta in domanda.risposte.all()
        ]
        domande_risposta.append({"domanda": domanda, "opzioni": opzioni})
    return domande_risposta


def form_scelta_partecipazione(request, back_url, utente_input="", quiz_input="", data_str=""):
    """Prepara il contesto e la risposta per la prima fase (scelta di utente, quiz
    e data): factorizzata perche riusata sia dalla richiesta GET iniziale sia dai
    percorsi di errore della seconda fase."""
    contesto = {
        "active": "partecipazioni",
        "titolo_pagina": "Nuova partecipazione",
        "modalita_modifica": False,
        "utenti": Utente.objects.order_by("nome_utente"),
        # Solo i quiz con almeno una domanda possono ricevere partecipazioni.
        "elenco_quiz": (
            Quiz.objects.annotate(n_domande=Count("domande"))
            .filter(n_domande__gt=0)
            .order_by("titolo")
        ),
        "valori": {"utente": utente_input, "quiz": quiz_input, "data": data_str},
        "url_annulla": "ricerca_partecipazioni",
        "back_url": back_url,
    }
    return render(request, "quiz/form_partecipazione.html", contesto)


def crea_partecipazione(request):
    """Gestisce la creazione di una nuova partecipazione in due fasi: prima si
    scelgono utente, quiz e data (fase "scelta", il form classico con
    autocompletamento), poi si risponde davvero a tutte le domande del quiz scelto
    (fase "risposte"); solo a quel punto partecipazione e risposte vengono salvate
    insieme in un'unica transazione."""
    back_url = url_ritorno_sicuro(request, "ricerca_partecipazioni")

    if request.method == "POST" and request.POST.get("fase") == "risposte":
        return salva_partecipazione_con_risposte(request, back_url)

    utente_input = ""
    quiz_input = ""
    data_str = ""

    if request.method == "POST":
        utente_input = request.POST.get("utente", "").strip()
        quiz_input = request.POST.get("quiz", "").strip()
        data_str = request.POST.get("data", "").strip()

        errori, utente, quiz, data_part = valida_partecipazione(
            utente_input, quiz_input, data_str
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
            # Utente, quiz e data sono validi: si passa alla fase di risposta alle
            # domande, senza ancora salvare nulla nel database.
            contesto = {
                "active": "partecipazioni",
                "titolo_pagina": "Rispondi al quiz",
                "utente": utente,
                "quiz": quiz,
                "data_part": data_part,
                "valori": {"utente": utente_input, "quiz": quiz_input, "data": data_str},
                "domande": costruisci_domande_risposta(quiz),
                "back_url": back_url,
            }
            return render(request, "quiz/rispondi_partecipazione.html", contesto)

        for errore in errori:
            messages.error(request, errore)

    return form_scelta_partecipazione(request, back_url, utente_input, quiz_input, data_str)


def salva_partecipazione_con_risposte(request, back_url):
    """Fase finale della creazione partecipazione: rivalida utente, quiz e data (per
    sicurezza, anche se gia validati nella prima fase) e le risposte scelte per
    ciascuna domanda del quiz, poi salva partecipazione e risposte in un'unica
    transazione, cosi da non lasciare mai una partecipazione senza risposte a meta."""
    utente_input = request.POST.get("utente", "").strip()
    quiz_input = request.POST.get("quiz", "").strip()
    data_str = request.POST.get("data", "").strip()

    errori, utente, quiz, data_part = valida_partecipazione(
        utente_input, quiz_input, data_str
    )

    if not errori:
        duplicata = Partecipazione.objects.filter(
            utente=utente, quiz=quiz, data=data_part
        ).exists()
        if duplicata:
            errori.append(
                "Esiste già una partecipazione di questo utente a questo quiz in questa data."
            )

    if errori:
        # Utente, quiz o data non sono (piu) validi: si torna alla prima fase,
        # mostrando gli errori raccolti.
        for errore in errori:
            messages.error(request, errore)
        return form_scelta_partecipazione(request, back_url, utente_input, quiz_input, data_str)

    # Verifica che sia stata scelta una risposta valida per ciascuna domanda del quiz,
    # tenendo traccia delle selezioni per poterle ripresentare in caso di errore.
    domande_risposta = costruisci_domande_risposta(quiz)
    errori_risposte = []
    risposte_valide = {}
    for voce in domande_risposta:
        domanda = voce["domanda"]
        valore_scelto = request.POST.get(f"risposta_domanda_{domanda.id}", "").strip()
        risposta_scelta = None
        for opzione in voce["opzioni"]:
            opzione["selezionata"] = str(opzione["risposta"].id) == valore_scelto
            if opzione["selezionata"]:
                risposta_scelta = opzione["risposta"]
        if risposta_scelta is None:
            errori_risposte.append(f"Selezionare una risposta per la domanda {domanda.numero}.")
        else:
            risposte_valide[domanda.id] = risposta_scelta

    if not errori_risposte:
        try:
            with transaction.atomic():
                partecipazione = Partecipazione(utente=utente, quiz=quiz, data=data_part)
                partecipazione.save()
                for voce in domande_risposta:
                    domanda = voce["domanda"]
                    RispostaUtenteQuiz.objects.create(
                        partecipazione=partecipazione,
                        domanda=domanda,
                        risposta=risposte_valide[domanda.id],
                    )
        except ValidationError as eccezione:
            aggiungi_errori_validazione(errori_risposte, eccezione)
        else:
            messages.success(request, "Partecipazione registrata correttamente con le risposte date.")
            return redirect(back_url)

    for errore in errori_risposte:
        messages.error(request, errore)

    contesto = {
        "active": "partecipazioni",
        "titolo_pagina": "Rispondi al quiz",
        "utente": utente,
        "quiz": quiz,
        "data_part": data_part,
        "valori": {"utente": utente_input, "quiz": quiz_input, "data": data_str},
        "domande": domande_risposta,
        "back_url": back_url,
    }
    return render(request, "quiz/rispondi_partecipazione.html", contesto)


def modifica_partecipazione(request, partecipazione_id):
    """Gestisce la modifica di una partecipazione esistente: utente e quiz non sono
    modificabili (cambiarli renderebbe incoerenti le risposte gia registrate) e sono
    quindi mostrati in sola lettura; eventuali valori inviati per quei campi vengono
    ignorati e l'unico campo validato/aggiornato e la data."""
    partecipazione = get_object_or_404(
        Partecipazione.objects.select_related("utente", "quiz"),
        pk=partecipazione_id,
    )
    back_url = url_ritorno_sicuro(request, "ricerca_partecipazioni")

    if request.method == "POST":
        data_str = request.POST.get("data", "").strip()

        errori, data_part = valida_data_partecipazione(data_str, partecipazione.quiz)

        # Il controllo duplicati esclude il record che si sta modificando,
        # altrimenti la partecipazione risulterebbe sempre in conflitto con se stessa.
        if not errori:
            duplicata = (
                Partecipazione.objects.filter(
                    utente=partecipazione.utente, quiz=partecipazione.quiz, data=data_part
                )
                .exclude(pk=partecipazione.pk)
                .exists()
            )
            if duplicata:
                errori.append(
                    "Esiste già una partecipazione di questo utente a questo quiz in questa data."
                )

        if not errori:
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

        valori = {"data": data_str}
    else:
        # Richiesta GET: precompila il form con la data attuale della partecipazione.
        valori = {"data": partecipazione.data.isoformat()}

    contesto = {
        "active": "partecipazioni",
        "titolo_pagina": "Modifica partecipazione",
        "modalita_modifica": True,
        "partecipazione": partecipazione,
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
