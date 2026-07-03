# Quiz Online - Progetto #2, gruppo BP Solutions
# Definisce lo schema dati dell'applicazione: utenti, quiz, domande, risposte
# e le partecipazioni degli utenti ai quiz con le relative risposte fornite.
from django.db import models


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

    def __str__(self):
        """Restituisce una descrizione sintetica della risposta data dall'utente."""
        return f"{self.partecipazione} - D{self.domanda.numero}"
