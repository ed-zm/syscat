from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render_to_response
from .forms import *
from django.views.generic import View
from .users import *
import pymongo

def post(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		print (username, password)
		if form.is_valid():
			return HttpResponseRedirect('/')
	else: 
		form = LoginForm
	return HttpResponse('hola')
def home(request):
	a = Users()
	usuario = a.show_user();
	print (usuario)
	return render_to_response('index.html', {'usuario' : usuario['_id']})