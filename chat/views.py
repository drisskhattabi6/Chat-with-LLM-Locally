from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from .models import Conversation, Message, DownloadedModel
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer, logging
from huggingface_hub import login
import re, markdown
import json
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

logging.set_verbosity_error()

login(token="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")

selected_llm = "gpt2"

def new_chat(request) :
    conversation = Conversation.objects.create(title="Conversation ")
    return redirect('chat_view', conversation_id=conversation.id)


def chat_view(request, conversation_id=None):
    conversation = messages = None
    global selected_llm
    error = None

    if request.method == "POST":
        user_message = request.POST.get('prompt')
        llm_path = request.POST.get('llm_path', "gpt2")

        if llm_path:
            selected_llm = llm_path

        # Check if the selected LLM is downloaded
        try:
            downloaded_model = DownloadedModel.objects.get(llm_name=selected_llm, is_downloaded=True)

            # Attempt to load the model and tokenizer
            try:
                model = AutoModelForCausalLM.from_pretrained(selected_llm)
                tokenizer = AutoTokenizer.from_pretrained(selected_llm)
                llm = pipeline('text-generation', model=model, tokenizer=tokenizer)
            except Exception as e:
                error = f"Failed to load the model '{selected_llm}'. It may not be available locally or is corrupted."
                print(f"Error loading model '{selected_llm}': {e}")

        except DownloadedModel.DoesNotExist:
            error = f"The selected model '{selected_llm}' is not available in the database."

        # Handle new conversation creation if conversation_id is not found or not provided
        if not error and user_message:
            if not conversation_id:
                # Create a new conversation
                conversation = Conversation.objects.create(title="Conversation ")

            # Save the user's message to the database
            user_message_obj = Message.objects.create(conversation=conversation, sender="user", content=user_message)

            # Generate the bot's response
            try:
                bot_response = llm(user_message, max_length=250, num_return_sequences=1, truncation=True)[0]['generated_text']
            except Exception as e:
                bot_response = "Sorry, I couldn't process your request at the moment."
                print(f"Error generating response: {e}")

            # Save the bot's response to the database
            Message.objects.create(conversation=conversation, sender="bot", content=bot_response)

            # Redirect to refresh the conversation page
            return redirect('chat_view', conversation_id=conversation.id)

    # If a conversation ID is provided, fetch the conversation and its messages
    if conversation_id:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        messages = conversation.messages.all()

    # Fetch all downloaded LLM options and conversations for the dropdown
    llm_options = DownloadedModel.objects.filter(is_downloaded=True)
    conversations = Conversation.objects.all()

    # Context for the template
    context = {
        'conversation': conversation,
        'messages': messages,
        'conversations': conversations,
        'llm_options': llm_options,
        'selected_llm': selected_llm,
        'error': error,
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
        llm_name = request.POST.get("llm_name", "").strip()

        if not llm_name:
            return JsonResponse({"success": False, "error": "Invalid LLM path."})

        # Check if the model is already downloaded
        downloaded_model, created = DownloadedModel.objects.get_or_create(llm_name=llm_name)

        if downloaded_model.is_downloaded:
            return JsonResponse({"success": False, "error": "Model already downloaded."})

        try:
            # Attempt to download the model and tokenizer
            AutoModelForCausalLM.from_pretrained(llm_name)
            AutoTokenizer.from_pretrained(llm_name)

            # Mark as downloaded in the database
            downloaded_model.is_downloaded = True
            downloaded_model.save()
            return JsonResponse({"success": True, "message": "Model downloaded successfully."})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error downloading model: {str(e)}"})

    return JsonResponse({"success": False, "error": "Invalid request method."})


def download_llm_page(request):
    llm_models = DownloadedModel.objects.all()
    context = {
        'llm_models': llm_models
    }
    return render(request, 'chat/download_llm.html', context)
