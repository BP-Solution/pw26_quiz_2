# Quiz Online - Progetto #2, gruppo BP Solutions
# Mappa gli URL dell'app quiz alle relative view: home, ricerche e CRUD partecipazioni.
from django.urls import path

from . import views

# Elenco delle rotte esposte dall'app, ciascuna associata a un nome
# usato dai template per generare i link tramite {% url %}.
urlpatterns = [
    path("", views.home, name="home"),
    path("utenti/", views.ricerca_utenti, name="ricerca_utenti"),
    path("utenti/<int:utente_id>/", views.dettaglio_utente, name="dettaglio_utente"),
    path("quiz/", views.ricerca_quiz, name="ricerca_quiz"),
    path("quiz/<int:quiz_id>/", views.dettaglio_quiz, name="dettaglio_quiz"),
    path("partecipazioni/", views.ricerca_partecipazioni, name="ricerca_partecipazioni"),
    path("partecipazioni/nuova/", views.crea_partecipazione, name="crea_partecipazione"),
    path("partecipazioni/<int:partecipazione_id>/", views.dettaglio_partecipazione, name="dettaglio_partecipazione"),
    path("partecipazioni/<int:partecipazione_id>/modifica/", views.modifica_partecipazione, name="modifica_partecipazione"),
    path("partecipazioni/<int:partecipazione_id>/elimina/", views.elimina_partecipazione, name="elimina_partecipazione"),
]
