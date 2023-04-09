from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi import Form, Cookie, status, File, UploadFile
from fastapi import Query
from fastapi.responses import FileResponse, RedirectResponse
from fastapi import Depends, Request, Response, status
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
import datetime
from passlib.hash import bcrypt
from datetime import timedelta
import database
from model import User
from app import app
import asyncio
from twilio.rest import Client
import config
import uuid
import secrets
from stripe import Webhook
from stripe.error import SignatureVerificationError
import stripe
import json
import os
from typing import List, Dict, Optional
from bson.objectid import ObjectId
from io import BytesIO
import io
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType
import base64
from PIL import Image
from pymongo import MongoClient
from bson import Binary
import time


settings = config.Settings()
client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

secretkey = secrets.token_hex(32)
stripe.api_key = "sk_test_51MgUmdAg9Km0gzmpEDI2M8ES9QLcec36ooBFJclyJ8m78Bqh2RlZ2I4JgsWmLsG2pbHy2LZ5ZtQIs9IPhuWCIVRL00xhD6zY9I"

print(settings.twilio_account_sid)
print(settings.twilio_auth_token)

SENDGRID_API_KEY = "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"

from database import (
    fetch_one_dash,
    fetch_all,
    create_dash,
    update_dash,
    remove_dash,
    fetch_one_event,
    fetch_all_events,
    fetch_all_events_by_approval1,
    create_event,
    update_event,
    remove_event,
    fetch_one_user,
    fetch_all_users,
    create_user,
    update_user,
    remove_user,
    get_event_count1,
    get_event_times,
    fetch_one_user_by_id,
    approve_event,
    fetch_one_product,
    fetch_one_product_byID,
    fetch_all_products,
    create_product,
    update_product,
    remove_product,
    update_user_active_field,
    user_image_upload,
    fetch_user_image,
    create_sup_ticket,
    fetch_unresolved_tickets,
    fetch_ticket,
    add_reply_to_ticket,
    get_categories,
    get_levels,
    get_locations,
    get_types,
    fetch_product_image,
    add_result,
    get_tickets_by_resolved_status,
    update_ticket_resolved_status,
    fetch_all_tickets,
)

from model import Dash, Ticket, Events, Fee, Contact, RowingResult, User, bankDetails, Item, Products, UserUpdateRequest, EmailData, SupportTicket, ReplyModel

origins = ["http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key= secretkey,
    max_age=timedelta(minutes=30),
)

@app.get("/")
def read_root():
    return {"Test":"Msg"}

#Results CRUD
@app.get("/api/dash")
async def get_dash():
    response = await fetch_all()
    return response

@app.get("/api/dash{name}", response_model=Dash)
async def get_dash_by_id(name):
    response = await fetch_one_dash(name)
    if response:
        return response
    raise HTTPException(404, f"There is no DASH item with this title: {name}")

@app.post("/api/dash", response_model=Dash)
async def post_dash(dash:Dash):
    response = await create_dash(dash.dict())
    if response:
        return response
    raise HTTPException(400, "Something went wrong / Bad Request")

@app.put("/api/dash{name}/", response_model=Dash)
async def put_dash(name:str, race_time:str):
    response = await update_dash(name, race_time)
    if response:
        return response
    raise HTTPException(400, "Something went wrong / Bad Request")


@app.delete("/api/dash{name}")
async def delete_dash(name):
    response = await remove_dash(name)
    if response:
        return "Successfully deleted Dash Item"
    raise HTTPException(400, "Something went wrong / Bad Request")



#Events CRUD
@app.get("/api/events")
async def get_events():
    response = await fetch_all_events()
    return response

@app.get("/api/events{name}", response_model=Events)
async def get_event_by_id(name):
    response = await fetch_one_event(name)
    if response:
        return response
    raise HTTPException(404, f"There is no Event item with this title: {name}")

@app.get("/api/events{approved}", response_model=List[Events])
async def get_events_by_approval1(approved: bool = False):
    response = []
    if approved:
        response = await fetch_all_events_by_approval1(approved)
    else:
        response = await fetch_all_events()
    if response:
        return response
    raise HTTPException(404, f"There are no events with status: {approved}")

@app.get("/api/events", response_model=List[Events])
async def get_filtered_events(
    search: Optional[str] = None,
    location: Optional[str] = None,
    date: Optional[str] = None,
    category: Optional[str] = None,
    event_type: Optional[str] = None,
    level: Optional[str] = None,
    ):
    events = await fetch_all_events()  # Assuming you have a function to fetch events from MongoDB
    filtered_events = []

    for event in events:
        if search and search.lower() not in event.name.lower():
            continue
        if location and location != event.location:
            continue
        if date:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            if not (event.event_start.date() <= date_obj.date() <= event.event_end.date()):
                continue
        if category and category != event.category:
            continue
        if event_type and event_type != event.type:
            continue
        if level and level != event.level:
            continue

        filtered_events.append(event)

    return filtered_events



@app.post("/api/events", response_model=Events)
async def post_event(events:Events):
    response = await create_event(events.dict())
    if response:
        return response
    raise HTTPException(400, "Something went wrong / Bad Request")

@app.put("/api/events{name}/", response_model=Events)
async def put_event(name:str, host_id:str, type:str, level:str, location: str, rower_limit:int, category:str,
            all_boat_classes:list, all_distances:list, gender_categories:dict, event_start:datetime.datetime,
            event_end:datetime.datetime, results: list[RowingResult], fee:Fee, contact:Contact, isComplete:bool, resultsUploaded:bool, approved:bool, description:str):
        response = await update_event(name, host_id, type, level, location, rower_limit, category, all_boat_classes, 
                all_distances, gender_categories, event_start, event_end, results, fee, contact, isComplete, resultsUploaded, approved, description)
        if response:
            return response
        raise HTTPException(400, "Something went wrong / Bad Request")

@app.delete("/api/events{name}")
async def delete_event(name):
    response = await remove_event(name)
    if response:
        return "Successfully deleted Event Item"
    raise HTTPException(400, "Something went wrong / Bad Request")

@app.get("/api/locations", response_model=List[str])
async def fetch_locations():
    locs = await get_locations()
    return locs

@app.get("/api/categories", response_model=List[str])
async def fetch_categories():
    cats = await get_categories()
    return cats

@app.get("/api/types", response_model=List[str])
async def fetch_types():
    types = await get_types()
    return types

@app.get("/api/levels", response_model=List[str])
async def fetch_levels():
    lvls = await get_levels()
    return lvls

@app.put("/api/events/{event_name}/add_result")
async def add_event_result(event_name: str, result: RowingResult):
    result_added = await add_result(event_name, result)
    if result_added:
        return {"detail": "Result added successfully."}
    else:
        return {"detail": "Event not found."}


#User CRUD
@app.get("/api/User")
async def get_users():
    response = await fetch_all_users()
    return response

@app.get("/api/User{name}", response_model=User)
async def get_user_by_id(name):
    response = await fetch_one_user(name)
    if response:
        return response
    raise HTTPException(404, f"There is no User item with this title: {name}")

@app.post("/api/User", response_model=User)
async def post_user(User:User):
    response = await create_user(User.dict())
    if response:
        return response
    raise HTTPException(400, "Something went wrong / Bad Request")

@app.put("/api/User{email}")
async def put_User(request: UserUpdateRequest):
    email = request.email
    name = request.name
    phone = request.phone
    dob = request.dob
    weight = request.weight
    club = request.club
    category = request.category
    location = request.location
    
    response = await update_user(email, name, phone, dob, weight, club, category, location)
    if response:
        return response
    raise HTTPException(400, "Something went wrong / Bad Request")

@app.delete("/api/User/{email}")
async def delete_user(email: str):
    response = await remove_user(email)
    if response:
        return "Successfully deleted user"
    raise HTTPException(400, "Failed to delete user")

@app.post("/api/User/image")
async def upload_user_img(email: str = Form(...), image: UploadFile = File(...)):
    res = await user_image_upload(email, image)
    return res

@app.get("/api/User/image/{email}", response_class=Response)
async def get_user_img(email: str):
    image_data = await fetch_user_image(email)
    if image_data:
        return StreamingResponse(io.BytesIO(image_data), media_type="image/png")
    else:
        return JSONResponse(content={"detail": f"There is no User with this email: {email}"}, status_code=404)

#REGISTER/LOGIN

@app.post("/api/User")
async def register_user(user: User):
    hashed_password = get_password_hash(user['password'])
    db_user = User(username=user['name'], email=user['email'], password=hashed_password)
    response = await create_user(db_user)
    return response

@app.post("/api/login")
async def login_user(user: User, request: Request):
    db_user = await fetch_one_user(user.email)
    if db_user and bcrypt.verify(user.password, db_user["password"]):
        session_id = generate_session_id()
        session = request.session
        session["user"] = user.email
        session["session_id"] = session_id
        print(session["user"])
        print(session["session_id"])
        return {"session_id": session_id, "status": f"success, logged in as {user.email}."}
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")

def generate_session_id():
    return str(uuid.uuid4())

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

@app.post('/api/register/{email}')
async def handle_form(email: str):
    await asyncio.get_event_loop().run_in_executor(
        None, send_verification_code, email)
    print("Test Print, from inside handle_form()")
    response = RedirectResponse('/verify',
                                status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie('email', email)
    print("Test Print2, from inside handle_form()")
    return response

def send_verification_code(email):
    verification = client.verify.services(
        settings.twilio_verify_service).verifications.create(
            to=email, channel='email')
    assert verification.status == 'pending'   

@app.get('/verify', response_class=HTMLResponse)
async def verify():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Z12 Performance - Verify your email</title>
        </head>
        <body>
            <h1>FastAPI Email Verification Example</h1>
            <form>
            <label for="code">Verification code:</label>
            <input name="code" id="code"/>
            <label for="email">Email:</label>
            <input name="email" id="email"/>
            <input type="submit" value="Submit"/>
            </form>
        </body>
    </html>
    """

def check_verification_code(email, code):
    verification = client.verify.services(
        settings.twilio_verify_service).verification_checks.create(
            to=email, code=code)
    return verification.status == 'approved'

@app.post('/verify')
async def verify_code(email: str = Query(...), code: str = Form(...)):
    verified = await asyncio.get_event_loop().run_in_executor(
        None, check_verification_code, email, code)
    print(f"Verification result for email {email} and code {code}: {verified}")
    if verified:
        updated_user = await update_user_active_field(email, True)
        if updated_user:
            print(f"User with email {updated_user.email} is now active")
        else:
            print(f"No user with email {email} found")
        
        return RedirectResponse('/success',
                                status_code=status.HTTP_303_SEE_OTHER)
    else:
        print(f"Failure to verify with email {email} and code {code}, status of verification: {verified}")
        return RedirectResponse('/verify',
                                status_code=status.HTTP_303_SEE_OTHER)

@app.get('/success')
async def success():
    # SET USER ACTIVE FLAG
    return {"message": "Verification successful"}
    

@app.get('/count')
async def get_event_count():
    tempCount = await get_event_count1()
    return tempCount

@app.get('/times')
async def read_times():
    times = await get_event_times()
    return {"times": times}

def calculate_order_amount(items):
    total_amount = 0
    for item in items:
        total_amount += int(item['productPrice'] * 100)
    return total_amount

@app.post('/create-payment-intent')
async def create_payment(request: Request):
    try:
        start_time = time.time()
        data = await request.json()
        end_time = time.time()
        print(f"Time taken to get JSON data: {end_time - start_time:.3f} seconds")

        start_time = time.time()
        items = data.get('items', [])
        amount = calculate_order_amount(items)
        
        end_time = time.time()
        print(f"Time taken to calculate order amount: {end_time - start_time:.3f} seconds")

        start_time = time.time()
        print("Before payment intent create")
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='eur',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        end_time = time.time()
        print(f"Time taken to create payment intent: {end_time - start_time:.3f} seconds")
        print("After payment intent create")

        start_time = time.time()
        response = JSONResponse({
            'clientSecret': intent['client_secret']
        })
        end_time = time.time()
        print(f"Time taken to create JSON response: {end_time - start_time:.3f} seconds")

        return response
    except Exception as e:
        return JSONResponse(content={'error': str(e)}, status_code=403)
    
@app.post('/create-payment-intent2')
async def create_payment2(request: Request):
    try:
        start_time = time.time()
        data = await request.json()
        end_time = time.time()
        print(f"Time taken to get JSON data: {end_time - start_time:.3f} seconds")

        start_time = time.time()
        items = data.get('items', [])
        amount = sum(item['price'] for item in items)

        
        end_time = time.time()
        print(f"Time taken to calculate order amount: {end_time - start_time:.3f} seconds")

        start_time = time.time()
        print("Before payment intent create")
        intent = stripe.PaymentIntent.create(
            amount=2000,
            currency='eur',
            payment_method_types=['card'],
            payment_method_data={
                'card': {
                    'number': '4242424242424242',
                    'exp_month': 12,
                    'exp_year': 2034,
                    'cvc': '567',
                    'name': 'John Doe'  # <-- fix parameter name here
                }
            }
        )
        end_time = time.time()
        print(f"Time taken to create payment intent: {end_time - start_time:.3f} seconds")
        print("After payment intent create")

        start_time = time.time()
        response = JSONResponse({
            'clientSecret': intent['client_secret']
        })
        end_time = time.time()
        print(f"Time taken to create JSON response: {end_time - start_time:.3f} seconds")

        return response
    except Exception as e:
        return JSONResponse(content={'error': str(e)}, status_code=403)
    
@app.post('/approve_events')
async def approve_events(event_names: List[str]):
    tempApproval = await approve_event(event_names)
    return tempApproval


#Product CRUD
@app.get("/api/products")
async def get_products():
    response = await fetch_all_products()
    return response

@app.get("/api/products{productName}", response_model=Products)
async def get_product_by_name(productName):
    response = await fetch_one_product(productName)
    if response:
        return response
    raise HTTPException(404, f"There is no Product item with this title: {productName}")

@app.get("/api/products/image/{productID}")
async def get_product_img(productID: str):
    image_data, image_extension = await fetch_product_image(productID)
    if image_data:
        base64_encoded_image = base64.b64encode(image_data).decode("utf-8")
        return {"productImage": base64_encoded_image, "productImageExtension": image_extension}
    raise HTTPException(404, f"There is no Product with this ID: {productID}")

@app.post("/api/products")
async def post_product(
    productName: str = Form(...),
    photographer: str = Form(...),
    productEvent: str = Form(...),
    productTags: str = Form(...),
    productPrice: float = Form(...),
    productCurrency: str = Form(...),
    productDate: str = Form(...),
    productImage: UploadFile = File(...),
    productID: Optional[str] = None
):
    productTagsList = [tag.strip() for tag in productTags.split(',')]
    productDateObj = datetime.datetime.strptime(productDate, "%Y-%m-%d").date()

    image_data = await productImage.read()
    img = Image.open(io.BytesIO(image_data))
    original_format = img.format
    

    productImageExtension = original_format.lower()
    binary_image_data = image_data

    if productID is None:
        productID = str(uuid.uuid4())

    product = Products(
        productName=productName,
        productID=productID,
        photographer=photographer,
        productEvent=productEvent,
        productTags=productTagsList,
        productPrice=productPrice,
        productCurrency=productCurrency,
        productDate=productDateObj,
        productImage=binary_image_data,
        productImageExtension=productImageExtension
    )
    response = await create_product(product.dict())
    if response:
        return response
    raise HTTPException(400, "Something went wrong / Bad Request")

@app.put("/api/products{productName}/", response_model=Products)
async def put_product(productName:str, productID:str, photographer:str, productEvent:str, productTags:List[str], productPrice:float,
                    productCurrency: str, productDate: datetime.date, productImage: bytes):
        response = await update_product(productName, productID, photographer, productEvent, productTags,
                                      productPrice, productCurrency, productDate, productImage)
        if response:
            return response
        raise HTTPException(400, "Something went wrong / Bad Request")

@app.delete("/api/products{productName}")
async def delete_product(productName):
    response = await remove_product(productName)
    if response:
        return "Successfully deleted Product Item"
    raise HTTPException(400, "Something went wrong / Bad Request")

@app.post("/send_product")
async def send_email(email_data: EmailData):
    if not SENDGRID_API_KEY:
        raise HTTPException(status_code=400, detail="SendGrid API Key not found")
    
    image_data = await fetch_one_product_byID(email_data.productID)
    if not image_data:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_binary = image_data['productImage']

    message = Mail(
        from_email="fitzgibbonsean2@gmail.com",
        to_emails=email_data.email,
        subject="Your Z12 Purchase",
        html_content="<strong>Thank you for your purchase, here is the product!</strong>"
    )

    image_encoded = base64.b64encode(image_binary).decode()

    attachment = Attachment(
        FileContent(image_encoded),
        FileName("image.jpg"),
        FileType("image/jpeg")
    )

    message.attachment = attachment

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")
    
    return {"status": "Email sent"}

@app.post("/tickets")
async def create_ticket(ticket: SupportTicket):
    ticket_id = await create_sup_ticket(ticket)
    return ticket_id

def ticket_to_dict(ticket: Dict) -> Dict:
    ticket["_id"] = str(ticket["_id"])
    return ticket

@app.get("/tickets/unresolved/")
async def get_active_tickets():
    tickets = await fetch_unresolved_tickets()
    return tickets

@app.get("/tickets/{ticket_id}/")
async def get_ticket(ticket_id: str):
    ticket = await fetch_ticket(ticket_id)
    return ticket_to_dict(ticket)

@app.post("/tickets/{ticket_id}/reply")
async def submit_reply(ticket_id: str, reply_data: ReplyModel):
    await add_reply_to_ticket(ticket_id, reply_data.reply)
    return {"message": "Reply submitted"}

@app.get('/tickets/', response_model=List[Ticket])
async def get_all_tickets():
    try:
        tickets = await fetch_all_tickets()
        return tickets
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get('/tickets/{resolved_status}/', response_model=List[Ticket])
async def get_tickets(resolved_status: str):
    if resolved_status not in ['resolved', 'unresolved']:
        raise HTTPException(status_code=400, detail="Invalid resolved status")

    is_resolved = resolved_status == 'resolved'
    tickets = await get_tickets_by_resolved_status(is_resolved)
    return tickets

@app.put('/tickets/{ticket_id}/resolve/')
async def mark_ticket_as_resolved(ticket_id: str):
    result = await update_ticket_resolved_status(ticket_id, True)

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"status": "success"}