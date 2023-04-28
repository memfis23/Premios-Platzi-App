import datetime

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    
    def __str__(self):
        return self.question_text
    
    def was_published_recently(self):
        return timezone.now() >= self.pub_date >= timezone.now() - datetime.timedelta(days=1)
    
    def save(self, *args, **kwargs):
        if self.pk is None and not self.pub_date:
            self.pub_date = timezone.now()
        super(Question, self).save(*args, **kwargs)
        
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    
    def __str__(self):
        return self.choice_text
