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
import io, calendar
from datetime import datetime, date, time, timedelta
from rlextra import rml2pdf

global active
active = False
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
def pagoexitoso(request):
	if active == True:
		if request.method == 'POST':
			hoy = datetime.now()
			ahora = hoy.strftime("%d/%m/%Y")
			ano = request.POST['ano']
			inscripcion = request.POST['inscripcion']
			trimestre = request.POST['trimestre']
			documento = users.update_document(ano, inscripcion, trimestre, ahora)
			return render_to_response('static/templates/pagoexitoso.html', {"usuario" : user})
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
	if active == True:
		if request.method == 'POST':
			iden = request.POST['texto_busqueda']
			busqueda = users.find_document(iden)
			if busqueda:
				b = busqueda[1]
				return render_to_response('static/templates/resultados.html', {"datos" : b, "usuario" : user})
			else:
				return render_to_response("static/templates/noencontrobusqueda.html", {"usuario": user})
		else: 
			return HttpResponse('Error Pagina no encontrada')
	else: 
		HttpResponseRedirect('/login')

def resultado_pago(request):
	if active == True:
		ac = False
		b = []
		if request.method == 'POST':
			iden = request.POST['texto_pago']
			connection_string = "mongodb://localhost"
			connection = pymongo.MongoClient(connection_string)
			db = connection.syscat
			pagos = db.pagos
			busqueda = users.find_document(iden)
			if busqueda is not False:
				m = busqueda[1]
				d= m['ubicacion_del_inmueble']['direccion']
				ni = m['numero_inscripcion']
			hoy = datetime.now()
			ano_actual = hoy.year
			for p in pagos.find({"numero_inscripcion" : iden}).sort("ano",1):
				if iden == p['numero_inscripcion']:
					ac = True
					ultimo = p
					ultimo_ano = p['ano']

			if ac == True:
				ano_ultimo = datetime.strptime(ultimo_ano, "%Y")
				an = ano_ultimo.year
				#print (an, ano_actual)
				while(ano_actual>an):
					pagos.insert
					an = an + 1
					#print (an)
				for p in pagos.find({"numero_inscripcion" : iden}).sort("ano",-1):
					b.append(p)
				return render_to_response ('static/templates/resultado_pago.html', {"resultados" : b, "usuario" : user, "direccion" : d, "numero_inscripcion": ni})
			else: 
				return render_to_response('static/templates/noencontropago.html', {"usuario" : user})
		else: 
			return HttpResponseRedirect('/login')

def reporte(request):
	if active == True:
		return render_to_response('static/templates/reporte.html', {"usuario" : user})
	else: 
		return HttpResponseRedirect('/login')
def generar_reporte(request):
	a = 0 
	b = []
	connection_string = "mongodb://localhost"
	connection = pymongo.MongoClient(connection_string)
	db = connection.syscat
	ficha_catastral = db.ficha_catastral
	t = get_template('r.html')
	for n in ficha_catastral.find():
		b.append(n)
		a = a + 1
	c = Context({"reporte": b, "total" : a})  
	rml = t.render(c)
	response = HttpResponse(rml, content_type='application/pdf')  
	response['Content-Disposition'] = 'attachment; filename=output.pdf'  
	return response 