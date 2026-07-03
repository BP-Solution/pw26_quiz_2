from datetime import date

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

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


def valida_partecipazione(utente_id, quiz_id, data_str):
    errori = []
    utente = None
    quiz = None
    data_part = None

    if not utente_id:
        errori.append("Selezionare un utente.")
    else:
        utente = Utente.objects.filter(pk=utente_id).first()
        if utente is None:
            errori.append("L'utente selezionato non esiste.")

    if not quiz_id:
        errori.append("Selezionare un quiz.")
    else:
        quiz = Quiz.objects.filter(pk=quiz_id).first()
        if quiz is None:
            errori.append("Il quiz selezionato non esiste.")

    if not data_str:
        errori.append("Inserire la data di partecipazione.")
    else:
        try:
            data_part = date.fromisoformat(data_str)
        except ValueError:
            errori.append("La data inserita non è valida.")

    if quiz is not None and data_part is not None:
        if data_part < quiz.data_inizio or data_part > quiz.data_fine:
            errori.append(
                f"La data deve essere compresa nel periodo di validità del quiz "
                f"({quiz.data_inizio.strftime('%d/%m/%Y')} – {quiz.data_fine.strftime('%d/%m/%Y')})."
            )

    return errori, utente, quiz, data_part


def crea_partecipazione(request):
    utente_id = ""
    quiz_id = ""
    data_str = ""

    if request.method == "POST":
        utente_id = request.POST.get("utente", "").strip()
        quiz_id = request.POST.get("quiz", "").strip()
        data_str = request.POST.get("data", "").strip()

        errori, utente, quiz, data_part = valida_partecipazione(
            utente_id, quiz_id, data_str
        )

        if not errori:
            duplicata = Partecipazione.objects.filter(
                utente=utente, quiz=quiz, data=data_part
            ).exists()
            if duplicata:
                errori.append(
                    "Esiste già una partecipazione di questo utente a questo quiz in questa data."
                )

        if not errori:
            Partecipazione.objects.create(
                utente=utente, quiz=quiz, data=data_part
            )
            messages.success(request, "Partecipazione creata correttamente.")
            return redirect("ricerca_partecipazioni")

        for errore in errori:
            messages.error(request, errore)

    contesto = {
        "active": "partecipazioni",
        "titolo_pagina": "Nuova partecipazione",
        "utenti": Utente.objects.order_by("nome_utente"),
        "elenco_quiz": Quiz.objects.order_by("titolo"),
        "valori": {"utente": utente_id, "quiz": quiz_id, "data": data_str},
        "url_annulla": "ricerca_partecipazioni",
    }
    return render(request, "quiz/form_partecipazione.html", contesto)


def modifica_partecipazione(request, partecipazione_id):
    partecipazione = get_object_or_404(
        Partecipazione.objects.select_related("utente", "quiz"),
        pk=partecipazione_id,
    )

    if request.method == "POST":
        utente_id = request.POST.get("utente", "").strip()
        quiz_id = request.POST.get("quiz", "").strip()
        data_str = request.POST.get("data", "").strip()

        errori, utente, quiz, data_part = valida_partecipazione(
            utente_id, quiz_id, data_str
        )

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
            partecipazione.save()
            messages.success(request, "Partecipazione modificata correttamente.")
            return redirect("ricerca_partecipazioni")

        for errore in errori:
            messages.error(request, errore)

        valori = {"utente": utente_id, "quiz": quiz_id, "data": data_str}
    else:
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
    }
    return render(request, "quiz/form_partecipazione.html", contesto)


def elimina_partecipazione(request, partecipazione_id):
    partecipazione = get_object_or_404(
        Partecipazione.objects.select_related("utente", "quiz"),
        pk=partecipazione_id,
    )

    if request.method == "POST":
        partecipazione.delete()
        messages.success(request, "Partecipazione eliminata correttamente.")
        return redirect("ricerca_partecipazioni")

    contesto = {
        "active": "partecipazioni",
        "partecipazione": partecipazione,
    }
    return render(request, "quiz/elimina_partecipazione.html", contesto)