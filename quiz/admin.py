# Quiz Online - Progetto #2, gruppo BP Solutions
# Registra i modelli dell'app quiz nel pannello di amministrazione Django.
from django.contrib import admin
from .models import Utente, Quiz, Domanda, Risposta, Partecipazione, RispostaUtenteQuiz

# Registrazione con la configurazione predefinita dell'admin, sufficiente
# per la gestione dei dati durante lo sviluppo e la demo del progetto.
admin.site.register(Utente)
admin.site.register(Quiz)
admin.site.register(Domanda)
admin.site.register(Risposta)
admin.site.register(Partecipazione)
admin.site.register(RispostaUtenteQuiz)