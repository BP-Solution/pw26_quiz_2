from django.shortcuts import render, get_object_or_404

from .models import Utente, Quiz, Domanda, Partecipazione


def home(request):
    contesto = {
        "active": "home",
        "n_utenti": Utente.objects.count(),
        "n_quiz": Quiz.objects.count(),
        "n_domande": Domanda.objects.count(),
        "n_partecipazioni": Partecipazione.objects.count(),
    }
    return render(request, "quiz/home.html", contesto)


def ricerca_utenti(request):
    utenti = Utente.objects.all().order_by("nome_utente")

    nome_utente = request.GET.get("nome_utente", "").strip()
    nome = request.GET.get("nome", "").strip()
    cognome = request.GET.get("cognome", "").strip()
    email = request.GET.get("email", "").strip()

    if nome_utente:
        utenti = utenti.filter(nome_utente__icontains=nome_utente)
    if nome:
        utenti = utenti.filter(nome__icontains=nome)
    if cognome:
        utenti = utenti.filter(cognome__icontains=cognome)
    if email:
        utenti = utenti.filter(email__icontains=email)

    contesto = {
        "active": "utenti",
        "utenti": utenti,
        "filtri": {
            "nome_utente": nome_utente,
            "nome": nome,
            "cognome": cognome,
            "email": email,
        },
    }
    return render(request, "quiz/ricerca_utenti.html", contesto)


def ricerca_quiz(request):
    elenco_quiz = Quiz.objects.select_related("creatore").order_by("titolo")

    titolo = request.GET.get("titolo", "").strip()
    creatore = request.GET.get("creatore", "").strip()
    data_da = request.GET.get("data_da", "").strip()
    data_a = request.GET.get("data_a", "").strip()

    if titolo:
        elenco_quiz = elenco_quiz.filter(titolo__icontains=titolo)
    if creatore:
        elenco_quiz = elenco_quiz.filter(creatore__nome_utente__icontains=creatore)
    if data_da:
        elenco_quiz = elenco_quiz.filter(data_inizio__gte=data_da)
    if data_a:
        elenco_quiz = elenco_quiz.filter(data_fine__lte=data_a)

    contesto = {
        "active": "quiz",
        "elenco_quiz": elenco_quiz,
        "filtri": {
            "titolo": titolo,
            "creatore": creatore,
            "data_da": data_da,
            "data_a": data_a,
        },
    }
    return render(request, "quiz/ricerca_quiz.html", contesto)


def dettaglio_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related("creatore"), pk=quiz_id
    )
    domande = quiz.domande.prefetch_related("risposte").order_by("numero")

    contesto = {
        "active": "quiz",
        "quiz": quiz,
        "domande": domande,
        "n_partecipazioni": quiz.partecipazioni.count(),
    }
    return render(request, "quiz/dettaglio_quiz.html", contesto)


def ricerca_partecipazioni(request):
    partecipazioni = Partecipazione.objects.select_related(
        "utente", "quiz"
    ).order_by("-data")

    utente = request.GET.get("utente", "").strip()
    titolo_quiz = request.GET.get("quiz", "").strip()
    data_da = request.GET.get("data_da", "").strip()
    data_a = request.GET.get("data_a", "").strip()

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

    contesto = {
        "active": "partecipazioni",
        "partecipazioni": partecipazioni,
        "filtri": {
            "utente": utente,
            "quiz": titolo_quiz,
            "data_da": data_da,
            "data_a": data_a,
        },
    }
    return render(request, "quiz/ricerca_partecipazioni.html", contesto)