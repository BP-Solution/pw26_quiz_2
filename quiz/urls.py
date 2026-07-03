from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("utenti/", views.ricerca_utenti, name="ricerca_utenti"),
    path("quiz/", views.ricerca_quiz, name="ricerca_quiz"),
    path("quiz/<int:quiz_id>/", views.dettaglio_quiz, name="dettaglio_quiz"),
    path("partecipazioni/", views.ricerca_partecipazioni, name="ricerca_partecipazioni"),
    path("partecipazioni/nuova/", views.crea_partecipazione, name="crea_partecipazione"),
    path("partecipazioni/<int:partecipazione_id>/modifica/", views.modifica_partecipazione, name="modifica_partecipazione"),
    path("partecipazioni/<int:partecipazione_id>/elimina/", views.elimina_partecipazione, name="elimina_partecipazione"),
]