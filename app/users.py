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
			u = self.ficha_catastral.find_one({"numero_inscripcion" : iden})
			if u['numero_inscripcion'] == iden:
				return True, u
			else:
				return False , None
		except:
			print ("No se pudo encontrar Numero")
			return False
	
	def update_document(self, ano, inscripcion, trimestre, ahora):
			if trimestre == "primero":
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.primero.status' : "Solvente", 'trimestre.primero.fecha' : ahora}})
				return True
			elif trimestre == "segundo":
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.segundo.status' : "Solvente", 'trimestre.segundo.fecha' : ahora}})
				return True
			elif trimestre == "tercero":
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.tercero.status' : "Solvente", 'trimestre.tercero.fecha' : ahora}})
				return True
			elif trimestre == "cuarto":
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.cuarto.status' : "Solvente", 'trimestre.cuarto.fecha' : ahora}})
				return True
			else:
				d = self.pagos.update_one({"numero_inscripcion": inscripcion, "ano" : ano}, {'$set' : {'trimestre.primero.status' : "Solvente", 'trimestre.segundo.status' : "Solvente", 'trimestre.tercero.status' : "Solvente", 'trimestre.cuarto.status' : "Solvente"}})