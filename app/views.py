from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext
from django.shortcuts import render_to_response
from django.views.generic import View
from django.core.context_processors import csrf
from .users import *
import pymongo


users = Users()
def admin(request):
	global active
	if active == True:
		return render_to_response('index.html', {'usuario' : user})
	else: 
		return HttpResponseRedirect('/login')


def auth(request):
	if request.method == 'POST':
		usuario_login = request.POST['usuario']
		password_login = request.POST['pass']
		usuario = users.find_user(usuario_login, password_login)
		if usuario:
			global active
			global user
			active = True
			user = usuario[1]
			return HttpResponseRedirect('/admin')
		else:
			global active
			active = False
			return HttpResponse("Usuario Inválido")
			#return HttpResponseRedirect('/login')"""
	else: 
		return HttpResponse('Error Pagina no encontrada')
	
def busqueda(request):
	if active == True:
		usuario = users.find_user()
		usuario_id = usuario['_id']
		return render_to_response('static/templates/busqueda.html')
	else: 
		return HttpResponseRedirect('/login')

def home(request): 
	global init
	init = True
	return HttpResponseRedirect('/login')

def login(request):
	c = {}
	c.update(csrf(request))
	return render_to_response('login.html', c)

def logout(request):
	global active
	active = False
	if active == False:
	 	return HttpResponseRedirect('/login')
	else: 
	 	return HttpResponse('página no encontrada')

def pagos(request):
	pass

def registro(request):
	usuario = users.find_user()
	usuario_id = usuario['_id']
	print ("estoy en registro")
	return render_to_response ('static/templates/registro.html',{'usuario' : usuario_id})

