from django.db import models

class Conversation(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Title : {self.title}, ID : {self.id}'


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=50)  # 'user' or 'bot'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"

# class LLM(models.Model) :
#     llm_name = models.CharField(max_length=255)

#     def __str__(self):
#         return f"LLM Name : {self.llm_name}"

class DownloadedModel(models.Model):
    llm_name = models.CharField(max_length=255, unique=True)
    is_downloaded = models.BooleanField(default=False)

    def __str__(self):
        return f"LLM Name : {self.llm_name}, is_downloaded : {self.is_downloaded}"