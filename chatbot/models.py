from django.db import models
from django.contrib.auth.models import User


class DocumentUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    is_indexed = models.BooleanField(default=False)
    indexing_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.filename

    class Meta:
        ordering = ['-upload_date']

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True, default="Nouvelle conversation")  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    document = models.ForeignKey(DocumentUpload, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.title or 'Conversation'} ({self.id})"

        
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
