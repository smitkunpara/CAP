import pymongo
from config import settings
from bson.objectid import ObjectId
from bson.json_util import dumps, loads
import json

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
        result = self.db.users.insert_one(user_data)
        return result.inserted_id
        
    def get_user(self, email):
        return self.db.users.find_one({"email": email})
    
    def update_user_token(self, email, token, refresh_token):
        result = self.db.users.update_one({"email": email}, {"$set": {"access_token": token, "refresh_token": refresh_token}})
        if result.matched_count > 0:
            return self.db.users.find_one({"email": email})["_id"]
        return None
    
    def add_user_email_analysis(self,user_id,email_analysis):
        self.db.users.insert_one({"user_id":ObjectId(user_id), "email_analysis":email_analysis})
    
    def get_user_email_analysis(self,user_id):
        return self.db.users.find({"user_id": ObjectId(user_id)})
    
    def add_email_analysis(self, user_id, email_analysis):
        self.db.email_analysis.insert_one({"user_id": ObjectId(user_id), "email_analysis": email_analysis})
        
    def get_email_analysis(self, email_id):
        # Find the document
        result = self.db.email_analysis.find_one({"_id": ObjectId(email_id)})
        
        # Convert to JSON serializable format
        if result:
            # Convert ObjectId to string and return a new dict
            result["_id"] = str(result["_id"])
            result["user_id"] = str(result["user_id"])
            return result
        return None
    
    def get_all_user_emails(self, user_id):
        user_emails= self.db.email_analysis.find({"user_id": ObjectId(user_id)})
        email_ids = []
        for email in user_emails:
            email_ids.append({"_id": str(email["_id"]), "subject": email["email_analysis"]["subject"]["subject"]})
        return email_ids

db=DataBase()