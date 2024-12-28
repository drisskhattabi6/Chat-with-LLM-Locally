from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Conversation, Message, DownloadedModel
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer, logging
from huggingface_hub import login
import re, markdown
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

logging.set_verbosity_error()

# Login to Hugging Face and Load the LLM
login(token="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")

# Initialize global variable for current llm
llm = pipeline('text-generation', model="gpt2")  # default LLM
# downloaded_models = set()

# # llm_path = "idrisskh/moroccan_recipes_chatbot_gemma_2b"
# llm_path = "gpt2"
# llm = pipeline('text-generation', model=llm_path)

def new_chat(request) :
    conversation = Conversation.objects.create(title="Conversation ")
    return redirect('chat_view', conversation_id=conversation.id)


""" def chat_view(request, conversation_id=None):
    conversation = messages = None

    if conversation_id:
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

    return render(request, 'chat/chat.html', context) """

def chat_view(request, conversation_id=None):
    conversation = messages = None

    # Fetch conversation and its messages if conversation_id is provided
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        messages = conversation.messages.all()

    if request.method == "POST":
        user_message = request.POST.get('prompt')
        llm_path = request.POST.get('llm_path', "gpt2")  # Default to "gpt2" if none provided

        # Check if the LLM is in the database and marked as downloaded
        try:
            downloaded_model = DownloadedModel.objects.get(llm_name=llm_path)

            # Attempt to load the model and tokenizer
            try:
                model = AutoModelForCausalLM.from_pretrained(llm_path)
                tokenizer = AutoTokenizer.from_pretrained(llm_path)
                llm = pipeline('text-generation', model=model, tokenizer=tokenizer)
            except Exception as e:
                # Handle errors during loading of the LLM
                print(f"Error loading model '{llm_path}': {e}")
                return render(request, 'chat/chat.html', {
                    'error': f"Failed to load the model '{llm_path}'. It may not be available locally or is corrupted.",
                    'conversation': conversation,
                    'messages': messages,
                })

        except DownloadedModel.DoesNotExist:
            # If the model is not found in the database
            return render(request, 'chat/chat.html', {
                'error': f"The selected model '{llm_path}' is not available in the database.",
                'conversation': conversation,
                'messages': messages,
            })

        # Generate a response if user_message is present
        if user_message:
            # Save user message to the database
            Message.objects.create(conversation=conversation, sender="user", content=user_message)

            # Generate the bot's response
            try:
                bot_response = llm(user_message, max_length=250, num_return_sequences=1, truncation=True)[0]['generated_text']
            except Exception as e:
                bot_response = "Sorry, I couldn't process your request at the moment."
                print(f"Error generating response: {e}")

            # Save bot response to the database
            Message.objects.create(conversation=conversation, sender="bot", content=bot_response)

            # Redirect to refresh the conversation page
            return redirect('chat_view', conversation_id=conversation.id)

    # Fetch all conversations and LLM options for the dropdown
    llm_options = DownloadedModel.objects.all()
    conversations = Conversation.objects.all()

    # Context for the template
    context = {
        'conversation': conversation,
        'messages': messages,
        'conversations': conversations,
        'llm_options': llm_options,
        'length_msgs': len(messages) if messages else 0,
    }
    return render(request, 'chat/chat.html', context)


def delete_chat(request, conversation_id=None):

    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        conversation.messages.all().delete()
        conversation.delete()

    return redirect('chat_view_no_id')


def download_llm(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        llm_path = data.get("llm_path")

        if not llm_path:
            return JsonResponse({"success": False, "error": "Invalid LLM path."})

        # Check if the model is already downloaded
        downloaded_model, created = DownloadedModel.objects.get_or_create(llm_name=llm_path)

        if downloaded_model.is_downloaded:
            return JsonResponse({"success": False, "error": "Model already downloaded."})

        try:
            # Download the model and tokenizer
            AutoModelForCausalLM.from_pretrained(llm_path)
            AutoTokenizer.from_pretrained(llm_path)

            # Mark as downloaded in the database
            downloaded_model.is_downloaded = True
            downloaded_model.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})


def download_llm_page(request):
    llm_models = DownloadedModel.objects.all()
    context = {
        'llm_models': llm_models
    }
    return render(request, 'chat/download_llm.html', context)
