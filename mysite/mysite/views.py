from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render

def home_page(request):
    return render(request, 'index.html')

def logout_page(request):
    """
    Log users out and re-direct them to the main page.
    """
    logout(request)
    return HttpResponseRedirect('/')

