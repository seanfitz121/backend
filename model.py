from pydantic import BaseModel, Field
import datetime
from typing import Optional, List
import base64

class Dash(BaseModel):
    name: str
    race_time: str


class RowingResult(BaseModel):
    user_id: str
    user_name: str
    position: int
    time: str

class Fee(BaseModel):
    currency: str
    amount: int

class Contact(BaseModel):
    contact_name: str
    contact_phone: str
    contact_email: str

class Events(BaseModel):
    _id: str
    name: str
    host_id: str
    type: str
    level: str
    location: str
    rower_limit: int
    category: str
    all_boat_classes: list
    all_distances: list
    gender_categories: dict
    event_start: datetime.datetime
    event_end: datetime.datetime
    results: list[RowingResult]
    fee: Fee
    contact: Contact
    isComplete: bool
    resultsUploaded: bool
    approved: bool
    description: str

class bankDetails(BaseModel):
    bank_detail1: str
    bank_detail2: str
    bank_detailx: str

class User(BaseModel):
    _id: str
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    password: str
    active: Optional[bool] = None
    image: Optional[bytes] = None
    dob: Optional[datetime.datetime] = None
    weight: Optional[float] = None
    club: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    bank_details: Optional[bankDetails] = None
    isAdmin: Optional[bool] = None
    type: Optional[str] = None

class UserUpdateRequest(BaseModel):
    email: str
    name: str
    phone: str
    dob: datetime.datetime
    weight: float
    club: str
    category: str
    location: str

class UserImageUpdateReq(BaseModel):
    email: str
    image: bytes
    
class Item(BaseModel):
    price: int

class Products(BaseModel):
    _id: str = Field(alias="_id")
    productName: str
    productID: str
    photographer: str
    productEvent: str
    productTags: Optional[List[str]] = None
    productPrice: float
    productCurrency: str
    productDate: Optional[datetime.date] = None
    productImage: Optional[bytes] = None
    productImageExtension: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
    
    def to_dict(self):
        product_dict = self.dict(by_alias=True, exclude={'productImage'})
        if "_id" in product_dict:
            product_dict["_id"] = str(product_dict["_id"])
        if self.productImage:
            product_dict["productImage"] = base64.b64encode(self.productImage).decode('utf-8')
        return product_dict

class EmailData(BaseModel):
    email: str
    productID: str

class SupportTicket(BaseModel):
    _id: str
    userName: str
    userEmail: str
    subject: str
    body: str
    timeSent: datetime.datetime
    timeResolved: Optional[datetime.datetime] = None
    replies: List[str] = []
    resolved: bool

class Ticket(BaseModel):
    _id: str
    userName: str
    subject: str
    body: str
    resolved: bool


class ReplyModel(BaseModel):
    reply: str