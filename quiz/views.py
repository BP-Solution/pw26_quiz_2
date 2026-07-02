from django.shortcuts import render

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