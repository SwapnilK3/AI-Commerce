"""
Authentication endpoints for Merchant Registration & Login.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from database import get_db
from models import Merchant
from auth import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class MerchantRegisterRequest(BaseModel):
    email: str
    password: str
    business_name: str
    merchant_name: str
    whatsapp_number: str = ""


@router.post("/register")
def register_merchant(request: MerchantRegisterRequest, db: Session = Depends(get_db)):
    """Register a new merchant account."""
    hashed_password = get_password_hash(request.password)
    
    new_merchant = Merchant(
        email=request.email,
        password_hash=hashed_password,
        business_name=request.business_name,
        merchant_name=request.merchant_name,
        whatsapp_number=request.whatsapp_number,
    )
    
    db.add(new_merchant)
    try:
        db.commit()
        db.refresh(new_merchant)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Automatically log them in
    access_token = create_access_token(data={"sub": new_merchant.id})
    
    return {
        "status": "success",
        "merchant": new_merchant.to_dict(),
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login a merchant to get an access token."""
    merchant = db.query(Merchant).filter(Merchant.email == form_data.username).first()
    
    if not merchant or not verify_password(form_data.password, merchant.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": merchant.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "merchant": merchant.to_dict()
    }
