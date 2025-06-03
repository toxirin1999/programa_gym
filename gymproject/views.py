# Basic view for home page
from django.shortcuts import render


def home(request):
    return render(request, 'home.html')
