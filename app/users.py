import pymongo
class Users:
	def __init__(self):
		connection_string = "mongodb://localhost"
		connection = pymongo.MongoClient(connection_string)
		db = connection.syscat
		self.db = db
		self.users = self.db.users
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
	#def insert_document(self, document)