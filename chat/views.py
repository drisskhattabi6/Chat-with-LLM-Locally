from django.shortcuts import render, redirect, get_object_or_404
from .models import Conversation, Message
from transformers import pipeline
from huggingface_hub import login
import re, markdown


# Login to Hugging Face and Load the LLM
login(token="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")

# llm_path = "idrisskh/moroccan_recipes_chatbot_gemma_2b"
llm_path = "gpt2"
llm = pipeline('text-generation', model=llm_path)


def new_chat(request) :
    conversation = Conversation.objects.create(title="Conversation ")
    return redirect('chat_view', conversation_id=conversation.id)


def chat_view(request, conversation_id=None):
    conversation = None
    messages = None

    if conversation_id:
        # if conversation_id == 'auto':
        #     pass
        # else:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        messages = conversation.messages.all()

    if request.method == "POST":
        user_message = request.POST.get('prompt')
        if user_message and conversation:
            # Store user message
            Message.objects.create(conversation=conversation, sender="user", content=user_message)

            # Generate bot response
            bot_response = llm(user_message, max_length=250, num_return_sequences=1, truncation=True)[0]['generated_text']

            # Remove the prompt from the generated response
            bot_response = bot_response.replace(user_message, '').strip()

            # Store bot message
            Message.objects.create(conversation=conversation, sender="bot", content=bot_response)

            return redirect('chat_view', conversation_id=conversation.id)
        
        elif user_message and conversation == None :

            conversation = Conversation.objects.create(title="Conversation ")
            Message.objects.create(conversation=conversation, sender="user", content=user_message)
            bot_response = llm(user_message, max_length=250, num_return_sequences=1, truncation=True)[0]['generated_text']
            bot_response = bot_response.replace(user_message, '').strip()

            # Store bot message
            Message.objects.create(conversation=conversation, sender="bot", content=bot_response)

            return redirect('chat_view', conversation_id=conversation.id)

    # Fetch all conversations for the sidebar
    conversations = Conversation.objects.all()

    length_msgs = 0
    if messages != None :
        length_msgs = len(messages)

    context = {
        'conversation': conversation,
        'messages': messages,
        'length_msgs': length_msgs,
        'conversations': conversations,
    }

    return render(request, 'chat/chat.html', context)


def delete_chat(request, conversation_id=None):

    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        conversation.messages.all().delete()
        conversation.delete()

    return redirect('chat_view_no_id')
