from django.db import models
from django.utils.timezone import now


# Create your models here.
class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return "{},{},({})".format(self.first_name, self.last_name, self.email)

    def get_name(self):
        fn = self.first_name
        if self.last_name == "-":
            ln = ""
        else:
            ln = self.last_name

        return fn + " " + ln


class Quiz(models.Model):
    quiz_name = models.CharField(max_length=100)
    max_marks = models.FloatField()
    participants = models.ManyToManyField(Student, through='Marks')

    def __str__(self):
        return self.quiz_name + " (MM: " + str(self.max_marks) + ")"


class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    marks = models.FloatField()

    def __str__(self):
        return "({}) {} ({}/{})".format(
            self.quiz.quiz_name,
            self.student.first_name,
            self.marks,
            self.quiz.max_marks
        )


class Log(models.Model):
    type = models.CharField(max_length=100)
    message = models.CharField(max_length=1000)
    datetime = models.DateTimeField(default=now)

    def __str__(self):
        datetime = self.datetime.strftime("%d-%B-%Y %I:%M %p")
        return "({}) {}/ {}".format(self.type, datetime, self.message[:100])