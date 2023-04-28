import datetime

from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Question, Choice


class QuestionModelTests(TestCase):
    
    def test_was_published_recently_with_future_questions(self):
        """was_published_recently return False for question whose pub_date is in the future"""
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(question_text="Quién es el mejor Course Director de Platzi", pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)
        
    def test_was_published_with_past_questions(self):
        """was_published_today return False for question whose pub_date is in the past"""
        time = timezone.now() + datetime.timedelta(days=-30)
        future_question = Question(question_text="Quién es el mejor Course Director de Platzi", pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)
        
    def test_was_published_with_right_now_questions(self):
        """was_published_today return True for question whose pub_date right now"""
        time = timezone.now()
        future_question = Question(question_text="Quién es el mejor Course Director de Platzi", pub_date=time)
        self.assertIs(future_question.was_published_recently(), True)
        
    def test_create_question_without_choices(self):
        """
        Intentar crear una pregunta sin opciones debe lanzar una excepción
        """
        question_text = "Pregunta sin opciones"
        pub_date = timezone.now()
        choice_text = "Opción 1"
        choice = Choice(choice_text=choice_text)
        question = Question(question_text=question_text, pub_date=pub_date)
        with self.assertRaises(ValueError):
            question.save()  # Intentar guardar la pregunta sin opciones debe lanzar una excepción
            question.choice_set.add(choice)  # Agregar opciones a la pregunta después de crearlas


def create_question(question_text, days):
    """
    Create a question with the given "question_text", and published the given
    number of days offset to now (negative for questions published in the past,
    positive for questions that have yet to be published)
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)
     
        
class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """If no question exist, an appropiate message is displayed"""
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context["latest_question_list"], [])
        
    def test_future_question(self):
        """
        Question with a pub_date in the future aren't displayed on the index page.
        """
        create_question("Future question", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context["latest_question_list"], [])
    
    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the index page
        """ 
        question = create_question("Past question", days=-10)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(response.context["latest_question_list"], [question])
             
    def test_future_question_and_past_question(self):
        """
        Even if both past and future question exist, only past questions are desplayed
        """
        past_question = create_question(question_text="Past question", days=-30)
        future_question = create_question(question_text="Past question", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(
            response.context["latest_question_list"],
            [past_question]
        )

    def test_two_past_questions(self):
        """The question index page may display multiple questions."""
        past_question1 = create_question(question_text="Past question 1", days=-30)
        past_question2 = create_question(question_text="Past question 2", days=-40)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(
            response.context["latest_question_list"],
            [past_question1, past_question2]
        )
        
    def test_two_future_questions(self):
        """The question index page may display multiple questions."""
        future_question1 = create_question(question_text="Past question 1", days=30)
        future_question2 = create_question(question_text="Past question 2", days=40)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(
            response.context["latest_question_list"],
            []
        )
        
        
class QuestionDetailViewTests(TestCase): 
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 error not found
        """
        future_question = create_question(question_text="Future question", days=30)
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text
        """
        past_question = create_question(question_text="Past question", days=-30)
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)
        
        
class ResultViewTests(TestCase):
    def test_no_questions(self):
        """
        If there are no questions, it displays an appropriate message.
        """
        response = self.client.get(reverse('polls:results', args=(1,)))
        self.assertEqual(response.status_code, 404)
    
    def test_question_without_choices(self):
        """
        If the question has no options, it displays an appropriate message.
        """
        question = Question.objects.create(question_text='¿Esta pregunta tiene opciones?')
        response = self.client.get(reverse('polls:results', args=(question.id,)))
        self.assertContains(response, "Esta pregunta no tiene opciones.", status_code=200)
    
    def test_question_with_choices(self):
        """
        If the question has options, it shows the options and their results.
        """
        question = Question.objects.create(question_text='¿Cuál es tu color favorito?')
        choice1 = Choice.objects.create(question=question, choice_text='Rojo')
        choice2 = Choice.objects.create(question=question, choice_text='Verde')
        response = self.client.get(reverse('polls:results', args=(question.id,)))
        self.assertContains(response, "¿Cuál es tu color favorito?", status_code=200)
        self.assertContains(response, "Rojo", status_code=200)
        self.assertContains(response, "0 votos", status_code=200)
        self.assertContains(response, "Verde", status_code=200)
        self.assertContains(response, "0 votos", status_code=200)
    
    def test_question_with_votes(self):
        """
        If the question has votes, it shows the options and their results.
        """
        question = Question.objects.create(question_text='¿Cuál es tu color favorito?')
        choice1 = Choice.objects.create(question=question, choice_text='Rojo')
        choice2 = Choice.objects.create(question=question, choice_text='Verde')
        choice1.votes = 2
        choice1.save()
        choice2.votes = 1
        choice2.save()
        response = self.client.get(reverse('polls:results', args=(question.id,)))
        self.assertContains(response, "¿Cuál es tu color favorito?", status_code=200)
        self.assertContains(response, "Rojo", status_code=200)
        self.assertContains(response, "2 votos", status_code=200)
        self.assertContains(response, "Verde", status_code=200)
        self.assertContains(response, "1 voto", status_code=200)