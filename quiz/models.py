from django.db import models


class Utente(models.Model):
    nome_utente = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=50)
    cognome = models.CharField(max_length=50)
    email = models.EmailField()

    def __str__(self):
        return self.nome_utente


class Quiz(models.Model):
    creatore = models.ForeignKey(Utente, on_delete=models.CASCADE, related_name="quiz_creati")
    titolo = models.CharField(max_length=200)
    data_inizio = models.DateField()
    data_fine = models.DateField()

    class Meta:
        verbose_name_plural = "Quiz"

    def __str__(self):
        return self.titolo


class Domanda(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="domande")
    numero = models.IntegerField()
    testo = models.TextField()

    class Meta:
        unique_together = ("quiz", "numero")

    def __str__(self):
        return f"{self.quiz} - D{self.numero}"


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
        return f"{self.domanda} - R{self.numero}"


class Partecipazione(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE, related_name="partecipazioni")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="partecipazioni")
    data = models.DateField()

    def __str__(self):
        return f"{self.utente} - {self.quiz}"


class RispostaUtenteQuiz(models.Model):
    partecipazione = models.ForeignKey(Partecipazione, on_delete=models.CASCADE, related_name="risposte_date")
    domanda = models.ForeignKey(Domanda, on_delete=models.CASCADE)
    risposta = models.ForeignKey(Risposta, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("partecipazione", "domanda")
        verbose_name_plural = "Risposte Utente Quiz"

    def __str__(self):
        return f"{self.partecipazione} - D{self.domanda.numero}"
