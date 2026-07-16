from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Domanda, Partecipazione, Quiz, Risposta, RispostaUtenteQuiz, Utente


class PartecipazioneValidationTests(TestCase):
    def setUp(self):
        oggi = timezone.localdate()
        self.utente = Utente.objects.create(
            nome_utente="mrossi",
            nome="Mario",
            cognome="Rossi",
            email="mario.rossi@example.com",
        )
        self.quiz = Quiz.objects.create(
            creatore=self.utente,
            titolo="Quiz valido",
            data_inizio=oggi - timedelta(days=5),
            data_fine=oggi + timedelta(days=5),
        )
        self.altro_quiz = Quiz.objects.create(
            creatore=self.utente,
            titolo="Altro quiz",
            data_inizio=oggi - timedelta(days=5),
            data_fine=oggi + timedelta(days=5),
        )
        self.domanda = Domanda.objects.create(
            quiz=self.quiz,
            numero=1,
            testo="Domanda del quiz valido",
        )
        self.risposta = Risposta.objects.create(
            domanda=self.domanda,
            numero=1,
            testo="Risposta corretta",
            tipo=Risposta.CORRETTA,
            punteggio=1,
        )
        self.altra_domanda = Domanda.objects.create(
            quiz=self.altro_quiz,
            numero=1,
            testo="Domanda dell'altro quiz",
        )
        self.altra_risposta = Risposta.objects.create(
            domanda=self.altra_domanda,
            numero=1,
            testo="Altra risposta",
            tipo=Risposta.CORRETTA,
            punteggio=1,
        )

    def test_partecipazione_non_accetta_data_futura(self):
        partecipazione = Partecipazione(
            utente=self.utente,
            quiz=self.quiz,
            data=timezone.localdate() + timedelta(days=1),
        )

        with self.assertRaisesMessage(ValidationError, "non può essere futura"):
            partecipazione.save()

    def test_partecipazione_non_accetta_data_fuori_periodo_quiz(self):
        partecipazione = Partecipazione(
            utente=self.utente,
            quiz=self.quiz,
            data=self.quiz.data_inizio - timedelta(days=1),
        )

        with self.assertRaisesMessage(ValidationError, "periodo di validità"):
            partecipazione.save()

    def test_non_si_puo_cambiare_quiz_se_esistono_risposte_collegate(self):
        partecipazione = Partecipazione.objects.create(
            utente=self.utente,
            quiz=self.quiz,
            data=timezone.localdate(),
        )
        RispostaUtenteQuiz.objects.create(
            partecipazione=partecipazione,
            domanda=self.domanda,
            risposta=self.risposta,
        )

        partecipazione.quiz = self.altro_quiz

        with self.assertRaisesMessage(ValidationError, "Non è possibile cambiare il quiz"):
            partecipazione.save()

    def test_risposta_utente_deve_appartenere_al_quiz_della_partecipazione(self):
        partecipazione = Partecipazione.objects.create(
            utente=self.utente,
            quiz=self.quiz,
            data=timezone.localdate(),
        )
        risposta_utente = RispostaUtenteQuiz(
            partecipazione=partecipazione,
            domanda=self.altra_domanda,
            risposta=self.altra_risposta,
        )

        with self.assertRaisesMessage(ValidationError, "non appartiene al quiz"):
            risposta_utente.save()

    def test_risposta_utente_deve_usare_risposta_della_domanda_indicata(self):
        partecipazione = Partecipazione.objects.create(
            utente=self.utente,
            quiz=self.quiz,
            data=timezone.localdate(),
        )
        risposta_utente = RispostaUtenteQuiz(
            partecipazione=partecipazione,
            domanda=self.domanda,
            risposta=self.altra_risposta,
        )

        with self.assertRaisesMessage(ValidationError, "non appartiene alla domanda"):
            risposta_utente.save()

    def test_creazione_mostra_errore_bootstrap_per_data_futura(self):
        response = self.client.post(
            reverse("crea_partecipazione"),
            {
                "utente": self.utente.nome_utente,
                "quiz": self.quiz.titolo,
                "data": (timezone.localdate() + timedelta(days=1)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La data di partecipazione non può essere futura.")
        self.assertContains(response, 'class="alert alert-danger"')

    def test_dettaglio_partecipazione_usa_next_locale_come_ritorno(self):
        partecipazione = Partecipazione.objects.create(
            utente=self.utente,
            quiz=self.quiz,
            data=timezone.localdate(),
        )
        back_url = reverse("dettaglio_quiz", args=[self.quiz.id])

        response = self.client.get(
            reverse("dettaglio_partecipazione", args=[partecipazione.id]),
            {"next": back_url},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{back_url}"')

    def test_next_esterno_viene_ignorato(self):
        partecipazione = Partecipazione.objects.create(
            utente=self.utente,
            quiz=self.quiz,
            data=timezone.localdate(),
        )

        response = self.client.get(
            reverse("dettaglio_partecipazione", args=[partecipazione.id]),
            {"next": "https://example.com/phishing"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{reverse("ricerca_partecipazioni")}"')
        self.assertNotContains(response, "https://example.com/phishing")


class CreazionePartecipazioneRisposteTests(TestCase):
    """Verifica il flusso in due fasi di creazione partecipazione: scelta di
    utente/quiz/data e successiva risposta a tutte le domande del quiz."""

    def setUp(self):
        oggi = timezone.localdate()
        self.utente = Utente.objects.create(
            nome_utente="lverdi",
            nome="Luca",
            cognome="Verdi",
            email="luca.verdi@example.com",
        )
        self.quiz = Quiz.objects.create(
            creatore=self.utente,
            titolo="Quiz con due domande",
            data_inizio=oggi - timedelta(days=5),
            data_fine=oggi + timedelta(days=5),
        )
        self.domanda1 = Domanda.objects.create(quiz=self.quiz, numero=1, testo="Prima domanda")
        self.risposta1_corretta = Risposta.objects.create(
            domanda=self.domanda1, numero=1, testo="Risposta corretta 1",
            tipo=Risposta.CORRETTA, punteggio=1,
        )
        Risposta.objects.create(
            domanda=self.domanda1, numero=2, testo="Risposta sbagliata 1",
            tipo=Risposta.SBAGLIATA,
        )
        self.domanda2 = Domanda.objects.create(quiz=self.quiz, numero=2, testo="Seconda domanda")
        self.risposta2_corretta = Risposta.objects.create(
            domanda=self.domanda2, numero=1, testo="Risposta corretta 2",
            tipo=Risposta.CORRETTA, punteggio=2,
        )

    def test_scelta_valida_mostra_la_pagina_di_risposta_con_le_domande(self):
        response = self.client.post(
            reverse("crea_partecipazione"),
            {
                "utente": self.utente.nome_utente,
                "quiz": self.quiz.titolo,
                "data": timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rispondi al quiz")
        self.assertContains(response, "Prima domanda")
        self.assertContains(response, "Seconda domanda")
        self.assertContains(response, f'name="risposta_domanda_{self.domanda1.id}"')

    def test_calendario_nativo_limita_il_periodo_e_conserva_i_campi(self):
        response = self.client.post(
            reverse("crea_partecipazione"),
            {
                "fase": "calendario",
                "utente": self.utente.nome_utente,
                "quiz": self.quiz.titolo,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="date" id="data" name="data"')
        self.assertContains(
            response, f'min="{self.quiz.data_inizio.isoformat()}"'
        )
        self.assertContains(
            response, f'max="{timezone.localdate().isoformat()}"'
        )
        self.assertContains(response, "Le altre date sono disabilitate nel calendario.")
        self.assertContains(response, f'value="{self.utente.nome_utente}"')
        self.assertContains(response, f'value="{self.quiz.titolo}"')

    def test_risposte_complete_creano_partecipazione_e_risposte(self):
        response = self.client.post(
            reverse("crea_partecipazione"),
            {
                "fase": "risposte",
                "utente": self.utente.nome_utente,
                "quiz": self.quiz.titolo,
                "data": timezone.localdate().isoformat(),
                f"risposta_domanda_{self.domanda1.id}": str(self.risposta1_corretta.id),
                f"risposta_domanda_{self.domanda2.id}": str(self.risposta2_corretta.id),
            },
        )

        self.assertRedirects(response, reverse("ricerca_partecipazioni"))
        partecipazione = Partecipazione.objects.get(utente=self.utente, quiz=self.quiz)
        risposte_registrate = RispostaUtenteQuiz.objects.filter(partecipazione=partecipazione)
        self.assertEqual(risposte_registrate.count(), 2)
        self.assertTrue(
            risposte_registrate.filter(
                domanda=self.domanda1, risposta=self.risposta1_corretta
            ).exists()
        )

    def test_risposta_mancante_non_salva_nulla_e_mostra_errore(self):
        response = self.client.post(
            reverse("crea_partecipazione"),
            {
                "fase": "risposte",
                "utente": self.utente.nome_utente,
                "quiz": self.quiz.titolo,
                "data": timezone.localdate().isoformat(),
                f"risposta_domanda_{self.domanda1.id}": str(self.risposta1_corretta.id),
                # manca volutamente la risposta alla seconda domanda
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selezionare una risposta per la domanda 2.")
        self.assertFalse(
            Partecipazione.objects.filter(utente=self.utente, quiz=self.quiz).exists()
        )
