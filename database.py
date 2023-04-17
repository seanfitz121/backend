from model import Dash, RowingResult, Fee, Contact, Events, User, Products, UserUpdateRequest, SupportTicket, ReplyModel;
#MongoDB Driver
import motor.motor_asyncio
from fastapi import FastAPI
from fastapi import HTTPException
from passlib.hash import bcrypt
from app import app
from fastapi.responses import JSONResponse
from bson import ObjectId
from typing import List, Optional, Dict
from bson.objectid import ObjectId
from datetime import datetime
from bson import Binary
from fastapi import File, UploadFile
import base64


client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017') #Replace with mongodb+srv://fitzgibbonsean2:z12fyp12@z12fyp.ahjo5iq.mongodb.net/?retryWrites=true&w=majority url when deploy
database = client.DashList
collection = database.dash

#Results CRUD
async def fetch_one_dash(name):
    document = await collection.find_one({"name":name})
    return document

async def fetch_all():
    dashes = []
    cursor = collection.find({})
    async for document in cursor:
        dashes.append(Dash(**document))
    return dashes

async def create_dash(dash):
    document = dash
    result = await collection.insert_one(document)
    return document

async def update_dash(name, race_time):
    await collection.update_one({"name":name},{"$set":{"race_time":race_time}})
    document = await collection.find_one({"name":name})
    return document

async def remove_dash(name):
    await collection.delete_one({"name":name})
    return True

#Events CRUD
async def fetch_one_event(name):
    document = await database.events.find_one({"name":name})
    return document

async def fetch_all_events():
    eventsL = []
    cursor = database.events.find({})
    async for document in cursor:
        eventsL.append(Events(**document))
    return eventsL

async def fetch_all_events_by_approval1(approved):
    eventsL = []
    cursor = database.events.find({"approved": bool(approved)})
    
    async for document in cursor:
        if document["approved"] == bool(approved):
            eventsL.append(Events(**document))
    return eventsL

async def create_event(events):
    document = events
    result = await database.events.insert_one(document)
    return document

async def update_event(name, host_id, type, level, location, rower_limit, category, all_boat_classes, all_distances,
                gender_categories, event_start, event_end, results, fee, contact, isComplete, resultsUploaded, approved, description):
    await database.events.update_one({"name":name},{"$set":{"host_id": host_id, "type": type, "level": level, "location": location, "rower_limit": rower_limit,
            "category": category, "all_boat_classes": all_boat_classes, "all_distances": all_distances, "gender_categories": gender_categories,
            "event_start": event_start, "event_end": event_end, "results": results, "fee": fee, "contact": contact, "isComplete": isComplete, "resultsUploaded": resultsUploaded, "approved": approved, "description": description}})
    document = await database.events.find_one({"name":name})
    return document

async def remove_event(name):
    await database.events.delete_one({"name":name})
    return True

async def get_locations() -> List[str]:
    events = database.events.find({}, {"_id": 0, "location": 1})
    locations = set()
    async for event in events:
        locations.add(event["location"])
    return sorted(locations)

async def get_categories() -> List[str]:
    events = database.events.find({}, {"_id": 0, "category": 1})
    categories = set()
    async for event in events:
        categories.add(event["category"])
    return sorted(categories)

async def get_types() -> List[str]:
    events = database.events.find({}, {"_id": 0, "type": 1})
    types = set()
    async for event in events:
        types.add(event["type"])
    return sorted(types)

async def get_levels() -> List[str]:
    events = database.events.find({}, {"_id": 0, "level": 1})
    levels = set()
    async for event in events:
        levels.add(event["level"])
    return sorted(levels)

async def add_result(event_name: str, result: RowingResult):
    event = await database.events.find_one({"name": event_name})
    if event:
        event["results"].append(result.dict())
        await database.events.update_one({"name": event_name}, {"$set": {"results": event["results"]}})
        return True
    else:
        return False


#User CRUD
#Fetch user by mail
async def fetch_one_user(email):
    document = await database.User.find_one({"email":email}, {"image": 0})
    return document

#Fetch user by ID
async def fetch_one_user_by_id(_id: str):
    document = await database.User.find_one({"_id": ObjectId(_id)})
    if not document:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    return document

async def fetch_all_users():
    usersL = []
    cursor = database.User.find({}, {"image": 0})
    async for document in cursor:
        usersL.append(User(**document))
    return usersL

class UserExistsError(Exception):
    pass

async def create_user(user: User):
    existing_user = await database.User.find_one({
        "$or": [
            {"email": user['email']},
            {"phone": user['phone']}
        ]
    })
    if existing_user:
        raise UserExistsError('Email or phone already associated with another user')

    user['password'] = bcrypt.hash(user['password'])
    result = await database.User.insert_one(user)
    user['_id'] = str(result.inserted_id)
    return User(**user)

async def update_user(email, name, phone, dob, weight, club, category,
                    location):
    
    await database.User.update_one({"email":email},{"$set":{"name": name, "phone": phone,
                         "dob": dob, "weight": weight, "club": club, "category": category, "location": location}})
    document = await database.User.find_one({"email":email})
    document.pop('_id', None)
    print(document)
    return document

async def remove_user(email):
    await database.User.delete_one({"email":email})
    return True

async def update_user_active_field(email: str, active: bool) -> Optional[User]:
    user = await database.User.find_one({'email': email})

    if user:
        user_id = user['_id']
        await database.User.update_one({'_id': ObjectId(user_id)}, {'$set': {'active': active}})
        updated_user = await database.User.find_one({'_id': ObjectId(user_id)})
        return User(**updated_user)
    else:
        return None

async def user_image_upload(email: str, image: UploadFile = File(...)):
    user_email = email
    user = database.User.find_one({"email": user_email})
    if user:
        image_data = await image.read()
        binary_image_data = Binary(image_data)
        database.User.update_one({"email": user_email}, {"$set": {"image": binary_image_data}})
        return {"message": "Image uploaded successfully"}
    else:
        return {"message": "User not found"}
    
async def fetch_user_image(email):
    user = await database.User.find_one({"email": email}, {"image": 1})
    if user is not None:
        return user["image"]
    else:
        return None


#Misc

async def get_event_count1():
    events = await database.events.find().to_list(None)
    counts = {}
    for event in events:
        if event["location"] in counts:
            counts[event["location"]] += 1
        else:
            counts[event["location"]] = 1
    return counts


async def get_event_times():
    results_list = database.events.find({}, {"_id": 0, "results": 1})
    times = []
    async for results in results_list:
        for result in results['results']:
            times.append(result['time'])
    return times

async def approve_event(event_names: List[str]):
    for event_name in event_names:
        event = await database.events.find_one({"name": event_name})
        if event:
            await database.events.update_one({"name": event_name}, {"$set": {"approved": True}})
    return {"message": "Event(s) approved successfully."}

#Product CRUD
async def fetch_one_product(name):
    document = await database.products.find_one({"productName":name})
    return document

async def fetch_all_products():
    productsL = []
    cursor = database.products.find({})
    async for document in cursor:
        
        if document.get("productImage"):
            document["productImage"] = base64.b64encode(document["productImage"])
        productsL.append(Products(**document))
    return productsL

async def create_product(product: dict):
    product['productDate'] = datetime.combine(product['productDate'], datetime.min.time())
    document = product
    result = await database.products.insert_one(document)
    document["_id"] = result.inserted_id

    product_instance = Products(**document)
    return product_instance.to_dict()

async def update_product(productName, productID, photographer, productEvent, productTags, productPrice, productCurrency, productDate, productImage):
    await database.products.update_one({"name":productName},{"$set":{"productName": productName, "productID": productID, "photographer": photographer,
                                                                   "productEvent": productEvent, "productTags": productTags, "productPrice": productPrice,
                                                                   "productCurrency": productCurrency, "productDate": productDate, "productImage": productImage}})
    document = await database.products.find_one({"name":productName})
    return document

async def remove_product(name):
    await database.products.delete_one({"name":name})
    return True

async def fetch_one_product_byID(productID):
    document = await database.products.find_one({"productID": productID})
    return document

async def fetch_product_image(productID: str):
    product = await database.products.find_one({"productID": productID}, {"productImage": 1, "productImageExtension": 1})
    if product:
        image_data = bytes(product["productImage"])
        image_extension = product["productImageExtension"]
        return image_data, image_extension
    return None, None

#Support tickets
ticket_collection = database.get_collection("tickets")

def ticket_helper(ticket) -> dict:
    return {
        "_id": str(ticket["_id"]),
        "userName": ticket["userName"],
        "subject": ticket["subject"],
        "body": ticket["body"],
        "resolved": ticket["resolved"],
    }

async def fetch_all_tickets():
    tickets = []
    async for ticket in ticket_collection.find():
        tickets.append(ticket_helper(ticket))
    return tickets

async def get_tickets_by_resolved_status(resolved: bool):
    tickets = []
    async for ticket in ticket_collection.find({"resolved": resolved}):
        tickets.append(ticket_helper(ticket))
    return tickets

async def update_ticket_resolved_status(ticket_id: str, resolved: bool):
    result = await ticket_collection.update_one(
        {"_id": ObjectId(ticket_id)}, {"$set": {"resolved": resolved}}
    )
    return result

async def create_sup_ticket(ticket: SupportTicket):
    ticket_id = await database.tickets.insert_one(ticket.dict())
    return {"id": str(ticket_id.inserted_id)}

def ticket_to_dict(ticket: Dict) -> Dict:
    ticket["_id"] = str(ticket["_id"])
    return ticket

async def fetch_unresolved_tickets():
    cursor = database.tickets.find({"resolved": False})
    tickets = await cursor.to_list(None)
    return [ticket_to_dict(ticket) for ticket in tickets]

async def fetch_ticket(ticket_id: str):
    ticket = await database.tickets.find_one({"_id": ObjectId(ticket_id)})
    return ticket

async def add_reply_to_ticket(ticket_id: str, reply: str):
    await database.tickets.update_one(
        {"_id": ObjectId(ticket_id)},
        {"$push": {"replies": reply}}
    )
