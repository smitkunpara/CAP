import pymongo
from config import settings
from bson.objectid import ObjectId

class DataBase:
    def __init__(self) -> None:
        try:
            self.client = pymongo.MongoClient(settings.DATABASE_URL)
            self.db = self.client[settings.DATABASE_NAME]
            print("Connected to MongoDB")
        except Exception as e:
            print(f"Error while connecting to MongoDB: {e}")
        
    def close_connection(self):
        self.client.close()
        print("MongoDB connection closed")
    
    def add_blacklisted_token(self, token):
        self.db.blacklistedtokens.insert_one({"token": token})
        
    def is_token_blacklisted(self, token):
        return self.db.blacklistedtokens.find_one({"token": token}) is not None
    
    def add_user(self, user_data):
        self.db.users.insert_one(user_data)
    
    def get_user(self, email):
        return self.db.users.find_one({"email": email})
    
    def update_user_token(self, email, token,refresh_token):
        self.db.users.update_one({"email": email}, {"$set": {"access_token": token,"refresh_token":refresh_token}})
    
    def add_user_email_analysis(self,user_id,email_analysis):#verify this funtion
        self.db.users.insert_one({"user_id":ObjectId(user_id), "email_analysis":email_analysis})
    
    def get_user_email_analysis(self,user_id):#verify this funtion
        return self.db.users.find({"user_id": ObjectId(user_id)})

db=DataBase()