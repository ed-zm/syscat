import pymongo
class Users:
	def __init__(self):
		connection_string = "mongodb://localhost"
		connection = pymongo.MongoClient(connection_string)
		db = connection.syscat
		self.db = db
		self.users = self.db.users
		self.ficha_catastral = self.db.ficha_catastral
		self.pagos = self.db.pagos
		self.ficha = self.db.ficha
		self.contador = self.db.contador
	def find_user(self, usuario_login, password_login):
		try: 
			u = None
			u = self.users.find_one({ "_id" : usuario_login, "password": password_login})
			if u['_id'] == usuario_login and u['password'] == password_login:
				return True, u['_id'], u['password']
			else:
				return False , None, None
		except:
			print ("No se pudo encontrar usuario")

	def find_document(self, iden):
		try:
			u = None
			u = self.ficha.find_one({"numero_inscripcion" : iden})
			if u['numero_inscripcion'] == iden:
				return True, u
			else:
				return False , None
		except:
			print ("No se pudo encontrar Numero")
			return False
	
	def find_pago(self, iden):
		try:
			u = None
			u = self.pagos.find_one({"numero_inscripcion" : iden})
			if u['numero_inscripcion'] == iden:
				return True, u
			else:
				return False , None
		except:
			print ("No se pudo encontrar Numero")
			return False

	def update_document(self, ano, inscripcion, trimestre, ahora, numero_factura):
		try:
			if trimestre == "primero":
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.primero.status' : "Solvente", 'trimestre.primero.fecha' : ahora, 'trimestre.primero.factura' : numero_factura}}, upsert = True)
				return True
			elif trimestre == "segundo":
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.segundo.status' : "Solvente", 'trimestre.segundo.fecha' : ahora, 'trimestre.segundo.factura' : numero_factura}}, upsert = True)
				return True
			elif trimestre == "tercero":
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.tercero.status' : "Solvente", 'trimestre.tercero.fecha' : ahora,'trimestre.tercero.factura' : numero_factura}},  upsert = True)
				return True
			elif trimestre == "cuarto":
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.cuarto.status' : "Solvente", 'trimestre.cuarto.fecha' : ahora, 'trimestre.cuarto.factura' : numero_factura}}, upsert = True)
				return True
			else:
				self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano, 'trimestre.primero.status' : "Pendiente"}, {'$set' : {'trimestre.primero.status' : "Solvente", 'trimestre.primero.fecha' : ahora, 'trimestre.primero.factura' : numero_factura}})
				self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano, 'trimestre.segundo.status' : "Pendiente"}, {'$set' : {'trimestre.segundo.status' : "Solvente", 'trimestre.segundo.fecha' : ahora, 'trimestre.segundo.factura' : numero_factura}})
				self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano, 'trimestre.tercero.status' : "Pendiente"}, {'$set' : {'trimestre.tercero.status' : "Solvente", 'trimestre.tercero.fecha' : ahora, 'trimestre.tercero.factura' : numero_factura}})
				self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano, 'trimestre.cuarto.status' : "Pendiente"}, {'$set' : {'trimestre.cuarto.status' : "Solvente", 'trimestre.cuarto.fecha' : ahora, 'trimestre.cuarto.factura' : numero_factura}})
				return True
		except Exception as e:
			print (e)
			return False

	def editar(self, inscripcion, valor_total_inmueble, observaciones_generales):
		try: 
			self.ficha.update_one({"numero_inscripcion" : inscripcion}, {"$set" : {"observaciones_generales" : observaciones_generales, "valoracion_economica_inmueble" : valor_total_inmueble}}, upsert = True)
			self.pagos.update_one({"numero_inscripcion" : inscripcion}, {"$set" : {"valoracion_economica_inmueble" : valor_total_inmueble}}, upsert = True)
			return True
		except Exception as e: 
			print ("no se pudo realizar por --editar--", e)
			return False

	def insertar_registro(self, dicc):
		try:
			r = self.ficha.insert_one(dicc)
			return True
		except Exception as e:
			return False
	def insertar_pago(self, f):
		try:
			p = self.pagos.insert_one(f)
			return True
		except Exception as e:
			return False

	def contar_ordenes(self):
		c = self.contador.update_one({"_id": "1"}, {"$inc" : {"cont" : 1}})
		encontrar = self.contador.find_one({"_id" : "1"})
		e = encontrar['cont']
		return e
	def contando_pagos(self):
		c = self.contador.update_one({"_id": "1"}, {"$inc" : {"cont_pagos" : 1}})
		encontrar = self.contador.find_one({"_id" : "1"})
		e = encontrar['cont_pagos']
		return e

	def total_pagos(self):
		encontrar = self.contador.find_one({"_id" : "1"})
		e = encontrar['cont_pagos']
		#print encontrar
		return e

	def encontrar_pago(self, iden):
		b = []
		datos = {}
		try:	
			for p in self.pagos.find({"numero_inscripcion" : iden}).sort("ano", 1):
				if iden == p['numero_inscripcion']:
					ultimo = p
					ultimo_ano = p['ano']
					b.append(p)
					datos['numero_inscripcion'] = p['numero_inscripcion'] 
					datos['ciudad_inmueble'] = p['ciudad_inmueble'] 
					datos['direccion_inmueble_op'] = p['direccion_inmueble_op'] 
					datos['direccion_inmueble'] = p['direccion_inmueble'] 
					datos['direccion_inmueble_entre'] = p['direccion_inmueble_entre'] 
					datos['direccion_inmueble_entre_op'] = p['direccion_inmueble_entre_op'] 
					datos['direccion_inmueble_y'] = p['direccion_inmueble_y'] 
					datos['direccion_inmueble_y_op'] = p['direccion_inmueble_y_op']
					datos['razon_social_propietario'] = p['razon_social_propietario']
					datos['cedula_o_rif_propietario'] = p['cedula_o_rif_propietario']
					datos['valoracion_economica_construccion'] = p['valoracion_economica_construccion']
					datos['valoracion_economica_inmueble'] = p['valoracion_economica_inmueble']
					return True, b, datos
				else:
					return False, b
		except Exception as e:
			print (e)
			return False, b

	def contar_pagos(self):
		total = 0
		for p in self.pagos.find():
			 if p['trimestre']['primero']['status'] == "Solvente":
			 	total = total + p['trimestre']['primero']['monto']
			 if p['trimestre']['segundo']['status'] == "Solvente":
			 	total = total + p['trimestre']['segundo']['monto']
			 if p['trimestre']['tercero']['status'] == "Solvente":
			 	total = total + p['trimestre']['tercero']['monto']
			 if p['trimestre']['cuarto']['status'] == "Solvente":
			 	total = total + p['trimestre']['cuarto']['monto']	
		return total


	def actualizar_monto(self, ano, valor_total_inmueble, inscripcion):
		try:
			self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano, "trimestre.primero.status" : "Pendiente"}, {'$set' : {'trimestre.primero.monto' : valor_total_inmueble}})
			self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano, "trimestre.segundo.status" : "Pendiente"}, {'$set' : {'trimestre.segundo.monto' : valor_total_inmueble}})
			self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano, "trimestre.tercero.status" : "Pendiente"}, {'$set' : {'trimestre.tercero.monto' : valor_total_inmueble}})
			self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano, "trimestre.cuarto.status" : "Pendiente"}, {'$set' : {'trimestre.cuarto.monto' : valor_total_inmueble}})			
			return True
		except Exception as e:
			print("no se pudo realizar por: --actualizar--", e)

	def count(self):
		c = self.ficha.count()
		return c
	def count_pagos(self):
		p = self.pagos.count()
		return p
