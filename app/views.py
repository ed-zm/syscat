from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext
from django.shortcuts import render_to_response
from django.views.generic import View
from django.core.context_processors import csrf
from .users import *
import pymongo

users = Users()
def admin(request):
	usuario = users.find_user();
	usuario_id = usuario['_id']
	return render_to_response('index.html', {'usuario' : usuario_id})

def auth(request):
	if request.method == 'POST':
		usuario = users.find_user()
		usuario_id = usuario['_id']
		usuario_login = request.POST['usuario']
		#password _login = request.POST['pass']
		print (request.POST['pass'], '=' ,{'usuario' : usuario_id})
		if usuario_id == usuario_login:
			print("este formulario es valido")
			return HttpResponseRedirect('/admin')
		else: 
			return HttpResponse('Pagina no encontrada')
	else: 
		return HttpResponse('Error Pagina no encontrada')
	
def busqueda(request):
	usuario = users.find_user()
	usuario_id = usuario['_id']
	return render_to_response('static/templates/busqueda.html', {'usuario' : usuario_id})

def home(request): 
	return HttpResponseRedirect('/login')

def login(request):
	c = {}
	c.update(csrf(request))
	return render_to_response('login.html', c)

def pagos(request):
	pass

def registro(request):
	usuario = users.find_user()
	usuario_id = usuario['_id']
	print ("estoy en registro")
	return render_to_response ('static/templates/registro.html',{'usuario' : usuario_id})

