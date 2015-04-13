import pymongo
class Users:
	def __init__(self):
		connection_string = "mongodb://localhost"
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
	def find_user(self):
		u = self.users.find_one()
		return u