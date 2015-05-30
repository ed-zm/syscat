from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.views.generic import View
from django.core.context_processors import csrf
from .users import *
import pymongo
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import StringIO
import io
#from io import cStringIO
from rlextra import rml2pdf
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
		return render_to_response('static/templates/busqueda.html', {"usuario" : user})
	else: 
		return HttpResponseRedirect('/login')

def exitoso(request):
	if active == True:
		return render_to_response('static/templates/exitoso.html', {"usuario" : user})

def home(request): 
	global init
	init = True
	return HttpResponseRedirect('/login')

def login(request):
	return render_to_response('login.html')

def logout(request):
	global active
	active = False
	if active == False:
	 	return HttpResponseRedirect('/login')
	else: 
	 	return HttpResponse('página no encontrada')

def pagos(request):
	if active == True:
		return render_to_response('static/templates/pagos.html', {"usuario" : user})
	else: 
		return HttpResponseRedirect('/login')
def registro(request):
	if active == True:
		return render_to_response ('static/templates/registro.html',{"usuario" : user})
	else:
		return HttpResponseRedirect('/login')

def registro_guardar(request):
	return HttpResponseRedirect('/exitoso')

def resultado(request):
	if request.method == 'POST':
		iden = request.POST['texto_busqueda']
		busqueda = users.find_document(iden)
		b = busqueda[1]
		#print (z)
		if busqueda:
			z = b['datos_propietario']
			ubicacion_del_inmueble = b['ubicacion_del_inmueble']
			direccion_del_inmueble = ubicacion_del_inmueble['direccion']
			return render_to_response('static/templates/resultados.html', {"direccion_del_inmueble" : direccion_del_inmueble})
		else:
			return HttpResponse("Numero no encontrado")
			#return HttpResponseRedirect('/login')"""
	else: 
		return HttpResponse('Error Pagina no encontrada')

def resultado_pago(request):
	if request.method == 'POST':
		iden = request.POST['texto_pago']
		connection_string = "mongodb://localhost"
		connection = pymongo.MongoClient(connection_string)
		db = connection.syscat
		pagos = db.pagos	
		for p in pagos.find({"numero_inscripcion" : iden}).sort({"ano" : "1"}):
			print (p)
		"""if u['numero_inscripcion'] == iden:
			return HttpResponse("Encontrado")
		else:
			return HttpResponse("pagina no encontrada")
	except:
		print ("No se pudo encontrar Numero")"""

def reporte(request):
	if active == True:
		return render_to_response('static/templates/reporte.html', {"usuario" : user})
	else: 
		return HttpResponseRedirect('/login')
def generar_reporte(request):
	a = 0 
	b = [0]
	connection_string = "mongodb://localhost"
	connection = pymongo.MongoClient(connection_string)
	db = connection.syscat
	ficha_catastral = db.ficha_catastral
	t = get_template('r.rml')
	for n in ficha_catastral.find():
		b.append(n)
		a = a + 1
	c = Context({"reporte": b, "total" : a})  
	rml = t.render(c)
	response = HttpResponse(rml, content_type='application/pdf')  
	response['Content-Disposition'] = 'attachment; filename=output.pdf'  
	return response 