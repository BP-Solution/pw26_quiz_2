# Quiz Online - Progetto #2, gruppo BP Solutions
# Definisce lo schema dati dell'applicazione: utenti, quiz, domande, risposte
# e le partecipazioni degli utenti ai quiz con le relative risposte fornite.
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# Rappresenta un utente registrato che puo creare quiz o parteciparvi.
class Utente(models.Model):
    nome_utente = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=50)
    cognome = models.CharField(max_length=50)
    email = models.EmailField()

    def __str__(self):
        """Restituisce il nome utente come rappresentazione testuale del modello."""
        return self.nome_utente


# Rappresenta un quiz creato da un utente, valido in un intervallo di date.
class Quiz(models.Model):
    creatore = models.ForeignKey(Utente, on_delete=models.CASCADE, related_name="quiz_creati")
    titolo = models.CharField(max_length=200)
    data_inizio = models.DateField()
    data_fine = models.DateField()

    class Meta:
        verbose_name_plural = "Quiz"

    def __str__(self):
        """Restituisce il titolo del quiz come rappresentazione testuale del modello."""
        return self.titolo


# Rappresenta una domanda appartenente a un quiz, numerata progressivamente.
class Domanda(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="domande")
    numero = models.IntegerField()
    testo = models.TextField()

    class Meta:
        unique_together = ("quiz", "numero")

    def __str__(self):
        """Restituisce una descrizione sintetica della domanda nel suo quiz."""
        return f"{self.quiz} - D{self.numero}"


# Rappresenta una possibile risposta a una domanda, corretta o sbagliata,
# con un punteggio associato solo per le risposte corrette.
class Risposta(models.Model):
    CORRETTA = "Corretta"
    SBAGLIATA = "Sbagliata"
    TIPO_SCELTE = [(CORRETTA, "Corretta"), (SBAGLIATA, "Sbagliata")]

    domanda = models.ForeignKey(Domanda, on_delete=models.CASCADE, related_name="risposte")
    numero = models.IntegerField()
    testo = models.TextField()
    tipo = models.CharField(max_length=10, choices=TIPO_SCELTE)
    punteggio = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    class Meta:
        unique_together = ("domanda", "numero")

    def __str__(self):
        """Restituisce una descrizione sintetica della risposta nella sua domanda."""
        return f"{self.domanda} - R{self.numero}"


# Rappresenta la partecipazione di un utente a un quiz in una determinata data.
class Partecipazione(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE, related_name="partecipazioni")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="partecipazioni")
    data = models.DateField()

    def clean(self):
        """Applica le regole di coerenza della partecipazione."""
        errori = {}

        if self.data and self.data > timezone.localdate():
            errori.setdefault("data", []).append("La data di partecipazione non può essere futura.")

        if self.quiz_id and self.data:
            quiz = self.quiz
            if self.data < quiz.data_inizio or self.data > quiz.data_fine:
                errori.setdefault("data", []).append(
                    "La data di partecipazione deve essere compresa nel periodo di validità "
                    f"del quiz ({quiz.data_inizio.strftime('%d/%m/%Y')} - {quiz.data_fine.strftime('%d/%m/%Y')})."
                )

        if self.pk and self.quiz_id:
            quiz_precedente_id = (
                Partecipazione.objects
                .filter(pk=self.pk)
                .values_list("quiz_id", flat=True)
                .first()
            )
            if quiz_precedente_id and quiz_precedente_id != self.quiz_id and self.risposte_date.exists():
                errori.setdefault("quiz", []).append(
                    "Non è possibile cambiare il quiz della partecipazione perché esistono già risposte collegate."
                )

        if errori:
            raise ValidationError(errori)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        """Restituisce una descrizione sintetica della partecipazione."""
        return f"{self.utente} - {self.quiz}"


# Registra la risposta scelta da un utente per una specifica domanda
# nell'ambito di una singola partecipazione a un quiz.
class RispostaUtenteQuiz(models.Model):
    partecipazione = models.ForeignKey(Partecipazione, on_delete=models.CASCADE, related_name="risposte_date")
    domanda = models.ForeignKey(Domanda, on_delete=models.CASCADE)
    risposta = models.ForeignKey(Risposta, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("partecipazione", "domanda")
        verbose_name_plural = "Risposte Utente Quiz"

    def clean(self):
        """Impedisce risposte riferite a domande o opzioni di un quiz diverso."""
        errori = {}

        if self.partecipazione_id and self.domanda_id:
            if self.domanda.quiz_id != self.partecipazione.quiz_id:
                errori.setdefault("domanda", []).append(
                    "La domanda selezionata non appartiene al quiz della partecipazione."
                )

        if self.domanda_id and self.risposta_id:
            if self.risposta.domanda_id != self.domanda_id:
                errori.setdefault("risposta", []).append(
                    "La risposta selezionata non appartiene alla domanda indicata."
                )

        if self.partecipazione_id and self.risposta_id:
            if self.risposta.domanda.quiz_id != self.partecipazione.quiz_id:
                errori.setdefault("risposta", []).append(
                    "La risposta selezionata non appartiene al quiz della partecipazione."
                )

        if errori:
            raise ValidationError(errori)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        """Restituisce una descrizione sintetica della risposta data dall'utente."""
        return f"{self.partecipazione} - D{self.domanda.numero}"
