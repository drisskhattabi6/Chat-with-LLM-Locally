from django.urls import path
from .views import *

urlpatterns = [
    path('', chat_view, name='home'),
    path('chat/<int:conversation_id>/', chat_view, name='chat_view'),
    path('chat/', chat_view, name='chat_view_no_id'),
    path('chat/new/', new_chat, name='chat_new'),
    path('delete/<int:conversation_id>/', delete_chat, name='delete_chat'),
    path('api/download_llm/', download_llm, name='download_llm'),
    path('download_llm/', download_llm_page, name='download_llm_page'),
]