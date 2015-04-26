import pymongo
class Users:
	def __init__(self):
		connection_string = "mongodb://localhost:28002"
		connection = pymongo.MongoClient(connection_string)
		db = connection.syscat
		self.db = db
		self.users = self.db.users
	def validate_login(self, username, password):
		user = ''
		try:
			user = self.users.find_one({'_id': username})
		except:
			print ("Unable to query database for user")
	def add_user(self, username, password, email):
		user = {'_id': username, 'password': password}
		if email != "":
			user['email'] = email
		try:
			self.users.insert_one(user)
		except pymongo.errors.OperationFailure:
			print ("oops, mongo error")
			return False
		except pymongo.errors.DuplicateKeyError as e:
			print ("oops, username is already taken")
			return False
		return True
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