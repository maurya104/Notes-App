import os
from groq import Groq
from nltk.corpus import stopwords
import nltk
from rake_nltk import Rake
from django.shortcuts import render, redirect
from django.db.models import Q
from .models import *
import bleach
from django import template

from django.shortcuts import get_object_or_404, HttpResponse
from heapq import nlargest
import re


import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from collections import Counter
from django.contrib.auth.decorators import login_required

register = template.Library()

@login_required
def home_view(request):
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    notes = Note.objects.filter(
        Q(title__icontains=q)).order_by("-updated", "-created")
    context = {"notes": notes}
    return render(request, "notePage/home.html", context)


def display_note(request, pk):
    note = Note.objects.get(id=pk)
    context = {"note": note}
    return render(request, "notePage/display-note.html", context)


def add_note(request):
    if request.method == "POST":
        Note(
            title=request.POST.get("title"),
            body=request.POST.get("body"),
        ).save()
        return redirect("home")
    return render(request, "notePage/edit-note.html")


def delete_note(request, pk):
    note = Note.objects.get(id=pk)
    if request.method == "POST":
        note.delete()
        return redirect("home")
    context = {"note": note}
    return render(request, "notePage/delete-note.html", context)


def edit_note(request, pk):
    note = Note.objects.get(id=pk)
    if request.method == "POST":
        note.title = request.POST.get("title")
        note.body = request.POST.get("body")
        note.save()
        return redirect("home")
    context = {"note": note}
    return render(request, "notePage/edit-note.html", context)


nlp = spacy.load('en_core_web_sm')


def clean_text(text):
    text = re.sub(r"'''", '', text)
    text = re.sub(r"‘’", '', text)
    text = re.sub(r'[\s]+', ' ', text)
    text = re.sub(r"—", '', text)
    text = re.sub(r"https?:\/\/\S+", '', text)
    text = re.sub(r"\@\w+", '', text)
    text = re.sub(r"\d+", '', text)
    return text.strip()


def summaries(request, pk):
    note = Note.objects.get(id=pk)
    text = clean_text(note.body)
    # print(text)
    doc = nlp(text)
    tokens = [token.text for token in doc]
    # print(tokens)
    punctuation = ''
    punctuation = punctuation + '\n                 '
    # print(punctuation)
    word_freq = {}
    stop_words = list(STOP_WORDS)
    for word in doc:
        if word.text.lower() not in stop_words and not word.is_punct:
            if word.text.lower() not in word_freq.keys():
                word_freq[word.text] = 1
            else:
                word_freq[word.text] += 1
        # print(word_freq)
    # print('max count :',max(word_freq.values()))

    for word in word_freq.keys():
        word_freq[word] = word_freq[word] / max(word_freq.values())
    # print(word_freq)

    sent_tokens = [sent for sent in doc.sents]
    # print(sent_tokens)

    sent_score = {}
    for sent in sent_tokens:
        for word in sent:
            if word.text.lower() in word_freq.keys():
                if sent not in sent_score.keys():
                    sent_score[sent] = word_freq[word.text.lower()]
                else:
                    sent_score[sent] += word_freq[word.text.lower()]
    # print(sent_score)

    summary = nlargest(n=3, iterable=sent_score, key=sent_score.get)
    print(summary)

    return render(request, 'notePage/summaries-page.html', {'summary': summary})


def pinNote(request, pk):
    note = get_object_or_404(Note, id=pk)
    note.is_pinned = not note.is_pinned
    note.save()
    return redirect('home')


simple_stopwords = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your',
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it',
    "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
    'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
    'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before',
    'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've',
    'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't",
    'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn',
    "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't",
    'wouldn', "wouldn't"
}


def remove_formatting(text):
    return re.sub(r'\*+', '', text)


def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text)
    keywords = [word for word in words if word.lower() not in simple_stopwords]
    return keywords


def highlight_keywords(text, keywords):
    for keyword in keywords:
        text = re.sub(rf'\b{keyword}\b', f'*{keyword}*',
                      text, flags=re.IGNORECASE)
    return text


def highlight(request, pk):
    note = Note.objects.get(id=pk)
    text = note.body
    cleaned_text = clean_text(text)
    client = Groq(
        api_key='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')

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Extract the main keywords from the following text: {cleaned_text}",
            }
        ],
        model="llama3-8b-8192",
    )

    text = chat_completion.choices[0].message.content
    keywords = extract_keywords(text)

    highlighted_text = highlight_keywords(text, keywords)

    # print(highlighted_text)

    clean_keyword = remove_formatting(highlighted_text)

    return render(request, "notePage/highlight.html", {'keyword': clean_keyword})

import json

# def check_grammer(request,pk):
    # note = Note.objects.get(id=pk)
    # text = note.body
    # cleaned_text = clean_text(text)
    # client = Groq(
    #     api_key='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')

    # chat_completion = client.chat.completions.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": f"Please check the spelling in the following text and provide corrections: {cleaned_text}",
    #         }
    #     ],
    #     model="llama3-8b-8192",
    # )
    # # miss_spell_list = chat_completion.choices[0].message['content']

    # response_message = chat_completion.choices[0].message.content
    # try:
    #     response_data = json.loads(response_message)
    #     misspelled_words = response_data.get('misspelled_words', [])
    #     suggestions = response_data.get('suggestions', {})
    # except (json.JSONDecodeError, TypeError):
        
    #     misspelled_words = []
    #     suggestions = {}

    # return render(request, "notePage/test.html", {
    #     'note': note,
    #     'misspelled_words': misspelled_words,
    #     'suggestions': suggestions
    # })
