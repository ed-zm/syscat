from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.views.generic import View
from django.core.context_processors import csrf
from .users import *
import pymongo
from django.http import HttpResponse
import io, calendar
from datetime import datetime, date, time, timedelta
from io import BytesIO
from reportlab.pdfgen import canvas



global active, invalido
invalido = False
active = False
users = Users()
def admin(request):
	global active
	if active == True:
		return render_to_response('index.html', {'usuario' : user})
	else: 
		return HttpResponseRedirect('/login')
from rlextra import rml2pdf

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
			invalido = True
			return render_to_response('login.html', {"invalido" : invalido})
	else:
		return HttpResponseRedirect('/login')
def busqueda(request):
	if active == True:
		return render_to_response('static/templates/busqueda.html', {"usuario" : user})
	else: 
		return HttpResponseRedirect('/login')

def confirmar_pago(request): 
	if active == True:
		ano = request.POST['ano']
		inscripcion = request.POST['inscripcion']
		trimestre = request.POST['trimestre']
		texto_pago = request.POST['iden']
		print (texto_pago)
		formu = {"ano" : ano, "inscripcion" : inscripcion, "trimestre" : trimestre, "texto_pago" : texto_pago}
		return render_to_response('static/templates/confirmar_pago.html', {"usuario" : user, "formu" : formu})
	else:
		return HttpResponseRedirect('/login')

def editar(request):
	if active == True:
		return render_to_response('static/templates/editar.html')
	else:
		return HttpResponseRedirect('/login')

def exitoso(request):
	if active == True:
		print (request.POST)
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
	 	return HttpResponseRedirect('/admin')

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
	if active == True:
		if request.method == 'POST':
			try:
				dicc = {}
				f = {}
				copy = request.POST.copy()
				req = copy.keys()
				post = copy
				cont = users.count()
				cont = cont +1
				post['_id'] = cont
				for p in req:
					dicc[p] = post[p]
					post[p]
				registro = users.insertar_registro(dicc)
				f['numero_inscripcion'] = copy['numero_inscripcion']
				f['ciudad_inmueble'] = copy['localidad']
				f['direccion_inmueble_op'] = copy['direccion_inmueble_op']
				f['direccion_inmueble'] = copy['direccion_inmueble']
				f['direccion_inmueble_entre'] = copy['direccion_inmueble_entre']
				f['direccion_inmueble_entre_op'] = copy['direccion_inmueble_entre_op']
				f['direccion_inmueble_y'] = copy['direccion_inmueble_y']
				f['direccion_inmueble_y_op'] = copy['direccion_inmueble_y_op']
				f['razon_social_propietario'] = copy['nombres_apellidos_o_razon_social_propietario']
				f['cedula_o_rif_propietario'] = copy['cedula_o_rif_propietario']
				f['valoracion_economica_construccion'] = copy['valoracion_economica_construccion']
				f['valoracion_economica_inmueble'] = copy['valoracion_economica_inmueble']
				f['trimestre']= {"primero": {"status": "Pendiente"}, "segundo":  {"status": "Pendiente"}, "tercero": {"status": "Pendiente"}, "cuarto": {"status": "Pendiente"}}
				hoy = datetime.now()
				ahora = hoy.strftime("%d/%m/%Y")
				ano = request.POST['ano']
				f['ano'] = ano
				ins = users.insertar_pago(f)
				print (ins)
				return HttpResponseRedirect('/exitoso')
			except Exception as e:
				return HttpResponse(e)
	else: 
		return HttpResponseRedirect('/login')

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
				while(ano_actual>an):
					an = an + 1
				for p in pagos.find({"numero_inscripcion" : iden}).sort("ano",-1):
					b.append(p)
				return render_to_response ('static/templates/resultado_pago.html', {"resultados" : b, "usuario" : user})
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
	if active == True:
		from rlextra.rml2pdf import rml2pdf
		a = 0 
		b = []
		connection_string = "mongodb://localhost"
		connection = pymongo.MongoClient(connection_string)
		db = connection.syscat
		ficha_catastral = db.ficha_catastral
		t = get_template('test_001_hello.rml') 
		for n in ficha_catastral.find():
			b.append(n)
			a = a + 1
		c = Context({"reporte": b, "total" : a})  
		rml = t.render(c)
		r = rml.encode('utf8')
		buf = BytesIO()
		sd = rml2pdf.go(r, outputFileName = buf)
		pdfData = buf.getvalue()
		response = HttpResponse(content_type='application/pdf')
		response.write(pdfData)
		response['Content-Disposition'] = 'attachment; filename="test_001_hello.pdf"'
		return response
	else:
		return HttpResponseRedirect('/login')

def orden_pago(request):
	if active == True:
		if request.method == 'POST':
			iden = request.POST['texto_pago']
			from rlextra.rml2pdf import rml2pdf
			print (iden)
			buscar_pago = users.find_pago(iden)
			formu = buscar_pago[1]
			t = get_template('orden_pago.rml')
			c = Context({"formu" : formu})
			rml = t.render(c)
			r = rml.encode('utf8')
			buf = BytesIO()
			rml2pdf.go(r, outputFileName = buf)
			pdfData = buf.getvalue()
			response = HttpResponse(content_type='application/pdf')
			response.write(pdfData)
			response['Content-Disposition'] = 'attachment; filename="orden_de_pago.pdf"'
			return response
	else:
		return HttpResponseRedirect('/login')

