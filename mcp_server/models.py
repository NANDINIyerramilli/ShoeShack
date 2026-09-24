from pydantic import BaseModel 

class Order(BaseModel): 
    id: int 
    user_id: str 
    product: str 
    status: str 
    amount: float 
    created_at: str 

class Ticket(BaseModel): 
    id: int 
    user_id: str 
    subject: str 
    description: str 
    status: str 
    priority: str 
    created_at: str 