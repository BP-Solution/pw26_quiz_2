from django.contrib import admin
from .models import Utente, Quiz, Domanda, Risposta, Partecipazione, RispostaUtenteQuiz

admin.site.register(Utente)
admin.site.register(Quiz)
admin.site.register(Domanda)
admin.site.register(Risposta)
admin.site.register(Partecipazione)
admin.site.register(RispostaUtenteQuiz)