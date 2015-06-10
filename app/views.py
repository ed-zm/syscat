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
		formu = {"ano" : ano, "inscripcion" : inscripcion, "trimestre" : trimestre, "texto_pago" : texto_pago}
		return render_to_response('static/templates/confirmar_pago.html', {"usuario" : user, "formu" : formu})
	else:
		return HttpResponseRedirect('/login')

def editar(request):
	if active == True:
		if request.method == 'POST':
			inscripcion = request.POST['inscripcion']
			valoracion_economica_inmueble = request.POST['valoracion_economica_inmueble']
			observaciones_generales = request.POST['observaciones_generales']
			return render_to_response('static/templates/editar.html',{"usuario" : user, "inscripcion" : inscripcion, "valoracion_economica_inmueble" : valoracion_economica_inmueble, "observaciones_generales" : observaciones_generales})
	else:
		return HttpResponseRedirect('/login')

def editar_exitoso(request):
	if active == True:
		if request.method == 'POST':
			inscripcion = request.POST['inscripcion']
			valor_total_inmueble = request.POST['valor_total_terreno']
			v = int(valor_total_inmueble)
			g = v *0.10
			observaciones_generales = request.POST['observaciones_generales']
			hoy = datetime.now()
			ano_actual = hoy.year
			ano = str(ano_actual)
			actualizar_monto = users.actualizar_monto(ano, g, inscripcion)
			busqueda = users.find_document(inscripcion)
			if busqueda:
				b = busqueda[1]
				concat = b["observaciones_generales"]
			observaciones = concat + " , " + observaciones_generales
			editar = users.editar(inscripcion, valor_total_inmueble, observaciones)
			if editar:
				return render_to_response("static/templates/exitoso.html", {"usuario" : user})
	else:
		return HttpResponseRedirect("/login")

def exitoso(request):
	if active == True:
		return render_to_response('static/templates/exitoso.html', {"usuario" : user})
	else:
		return HttpResponseRedirect("/login")

def mal(request):
	if active == True:
		return render_to_response('static/templates/mal.html', {"usuario" : user})
	else:
		return HttpResponseRedirect("/login")


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
			numero_factura = request.POST['numero_factura']
			documento = users.update_document(ano, inscripcion, trimestre, ahora, numero_factura)
			if documento:
				e = users.contando_pagos()
				print (e)
				return render_to_response('static/templates/pagoexitoso.html', {"usuario" : user})
			else: 
				return HttpResponse("nada")
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
				cont_pago = users.count_pagos()
				cont_pago = cont_pago+1
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
				f['direccion_propietario_op'] = copy['direccion_propietario_op']
				f['direccion_propietario'] = copy['direccion_propietario']
				f['direccion_propietario_entre_op'] = copy['direccion_propietario_entre_op']
				f['direccion_entre_propietario'] = copy['direccion_entre_propietario']
				f['direccion_y_propietario_op'] = copy['direccion_y_propietario_op']
				f['direccion_y_propietario'] = copy['direccion_y_propietario']
				f['sector'] = copy['sector']
				f['parroquia'] = copy['parroquia']
				f['lindero_norte'] = copy['lindero_norte']
				f['lindero_sur'] = copy['lindero_sur']
				f['lindero_este'] = copy['lindero_este']
				f['lindero_oeste'] = copy['lindero_oeste']
				f['telefono_propietario'] = copy['telefono_propietario']
				f['codigo_catastral'] = copy['codigo_catastral']
				f['valoracion_economica_area_total'] = copy['valoracion_economica_area_total']
				ch = int(copy['valoracion_economica_inmueble'])
				g =  ch* 0.10
				f['trimestre']= {"primero": {"status": "Pendiente", "monto" : g}, "segundo":  {"status": "Pendiente", "monto" : g}, "tercero": {"status": "Pendiente", "monto" : g}, "cuarto": {"status": "Pendiente", "monto" : g}}
				f['_id'] = cont_pago
				hoy = datetime.now()
				ahora = hoy.strftime("%d/%m/%Y")
				ano_actual = hoy.year
				ano = str(ano_actual)
				#ano = request.POST['ano']
				f['ano'] = ano
				ins = users.insertar_pago(f)
				if registro and ins:
					return HttpResponseRedirect('/exitoso')
				else:
					return HttpResponseRedirect('/mal')
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
			pago = users.encontrar_pago(iden)
			hoy = datetime.now()
			ano_actual = hoy.year
			"""if ac == True:
				ano_ultimo = datetime.strptime(ultimo_ano, "%Y")
				an = ano_ultimo.year
				while(ano_actual>an):
					an = an + 1"""
			if pago:
				datos = pago[2]
				pagos = pago[1]
				return render_to_response ('static/templates/resultado_pago.html', {"resultados" : pagos, "usuario" : user, "datos" : datos, "iden" : iden})
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
		hoy = datetime.now()
		ahora = hoy.strftime("%d/%m/%Y")
		from rlextra.rml2pdf import rml2pdf
		t = get_template('reporte.rml')
		total_dinero = users.contar_pagos() 
		total_usuarios = users.count()
		total_pagos = users.total_pagos()
		c = Context({"total_pagos" : total_pagos, "total_dinero" : total_dinero, "total_usuarios" : total_usuarios, "ahora" : ahora})  
		rml = t.render(c)
		r = rml.encode('utf8')
		buf = BytesIO()
		sd = rml2pdf.go(r, outputFileName = buf)
		pdfData = buf.getvalue()
		response = HttpResponse(content_type='application/pdf')
		response.write(pdfData)
		salida = "attachment; filename="
		nombresalida = salida + "reporte_" + ahora + ".pdf"
		response['Content-Disposition'] = nombresalida
		#'attachment; filename="orden_de_pago.pdf"'
		return response
	else:
		return HttpResponseRedirect('/login')

def orden_pago(request):
	if active == True:
		if request.method == 'POST':
			total = 0
			ano = request.POST['ano']
			inscripcion = request.POST['inscripcion']
			trimestre = request.POST['trimestre']
			adquiriente = request.POST['adquiriente']
			cedula_o_rif_adquiriente = request.POST['cedula_o_rif_adquiriente']
			hoy = datetime.now()
			ano_actual = hoy.year
			ano = str(ano_actual)
			ahora = hoy.strftime("%d/%m/%Y")
			formu = users.encontrar_pago(inscripcion)
			form = formu[1]
			form1 = form[0]
			contador = users.contar_ordenes()
			total_primero = int(form1['trimestre']['primero']['monto'])
			total_segundo = int(form1['trimestre']['segundo']['monto'])
			total_tercero = int(form1['trimestre']['tercero']['monto'])
			total_cuarto = int(form1['trimestre']['cuarto']['monto'])
			if form1['trimestre']['primero']['status'] == "Pendiente":
				total = total+total_primero
			if form1['trimestre']['segundo']['status'] == "Pendiente":
				total = total+total_segundo
			if form1['trimestre']['tercero']['status'] == "Pendiente":
				total = total+total_tercero
			if form1['trimestre']['cuarto']['status'] == "Pendiente":
				total = total+total_cuarto 
			cedula = form1['cedula_o_rif_propietario']
			from rlextra.rml2pdf import rml2pdf
			t = get_template('orden_pago.rml')
			c = Context({"formu" : form1, "ahora" : ahora, "ano": ano, "adquiriente": adquiriente, "cedula_o_rif_adquiriente" : cedula_o_rif_adquiriente, "total" : total, "trimestre" : trimestre, "numero_orden" : contador})
			rml = t.render(c)
			r = rml.encode('utf8')
			buf = BytesIO()
			rml2pdf.go(r, outputFileName = buf)
			pdfData = buf.getvalue()
			response = HttpResponse(content_type='application/pdf')
			response.write(pdfData)
			salida = "attachment; filename="
			nombresalida = salida + "orden_pago_" + cedula + ".pdf"
			response['Content-Disposition'] = nombresalida
			#'attachment; filename="orden_de_pago.pdf"'
			return response
	else:
		return HttpResponseRedirect('/login')

