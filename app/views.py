from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render_to_response
from .forms import *
from django.views.generic import View
from .users import *
import pymongo

def auth(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		a = Users()
		usuario = a.find_user()
		usuario_post = request.POST['usuario']
		if form.is_valid():
			if usuario_post == usuario:
				print (request.POST['usuario'])
				return HttpResponseRedirect('/')
	else: 
		form = LoginForm()
	return HttpResponse('Error Pagina no encontrada')
def home(request):
	a = Users()
	usuario = a.find_user();
	print (usuario)
	return render_to_response('index.html', {'usuario' : usuario['_id']})