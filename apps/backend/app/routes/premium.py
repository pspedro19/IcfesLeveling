from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
# import stripe  # Temporalmente comentado para desarrollo
from typing import Optional
import os

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..schemas.premium import (
    CreateCheckoutSession,
    PaymentIntentCreate,
    PaymentIntentResponse,
    SubscriptionResponse,
    WebhookEvent
)

router = APIRouter(prefix="/premium", tags=["premium"])

# Configure Stripe
# stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")  # Temporalmente comentado
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

@router.post("/create-checkout-session")
async def create_checkout_session(
    data: CreateCheckoutSession,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Checkout session for premium subscription"""
    try:
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': data.priceId,
                'quantity': 1,
            }],
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
            success_url=f"{os.getenv('FRONTEND_URL')}/premium/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL')}/premium/cancel",
            metadata={
                'user_id': str(current_user.id),
                'plan_id': data.planId
            }
        )
        
        return {"sessionId": session.id}
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    data: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent for one-time purchases"""
    try:
        intent = stripe.PaymentIntent.create(
            amount=data.amount,
            currency=data.currency,
            metadata={
                'user_id': str(current_user.id)
            }
        )
        
        return PaymentIntentResponse(
            clientSecret=intent.client_secret,
            amount=intent.amount,
            currency=intent.currency
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        plan_id = session['metadata']['plan_id']
        
        # Update user premium status
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_premium = True
            user.premium_plan = plan_id
            
            # Set expiration based on plan
            if plan_id == 'monthly':
                user.premium_expires_at = datetime.utcnow() + timedelta(days=30)
            elif plan_id == 'yearly':
                user.premium_expires_at = datetime.utcnow() + timedelta(days=365)
            
            # Add bonus for new premium users
            user.orbs += 1000  # Bonus orbs
            user.ai_requests_limit = 100  # Increased AI requests
            user.simulacros_limit = -1  # Unlimited simulacros
            
            db.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Handle subscription cancellation
        # Find user by customer ID and update premium status
        
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Handle successful one-time payment
        
    return {"status": "success"}

@router.get("/subscription/{user_id}", response_model=SubscriptionResponse)
async def get_user_subscription(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's subscription details"""
    # Check if requesting user is the same or admin
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this subscription"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return SubscriptionResponse(
        is_premium=user.is_premium,
        premium_plan=user.premium_plan,
        premium_expires_at=user.premium_expires_at,
        ai_requests_used=user.ai_requests_used,
        ai_requests_limit=user.ai_requests_limit,
        simulacros_used=user.simulacros_used,
        simulacros_limit=user.simulacros_limit
    )

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel user's premium subscription"""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    # Here you would cancel the Stripe subscription
    # For now, just update the user's status
    current_user.is_premium = False
    current_user.premium_plan = None
    current_user.premium_expires_at = None
    current_user.ai_requests_limit = 5  # Reset to free tier
    current_user.simulacros_limit = 2
    
    db.commit()
    
    return {"message": "Subscription cancelled successfully"}

@router.get("/payment-history/{user_id}")
async def get_payment_history(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's payment history"""
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment history"
        )
    
    # Here you would fetch from Stripe or your payment history table
    # For now, return mock data
    return {
        "payments": [
            {
                "id": "pay_123",
                "amount": 19900,
                "currency": "COP",
                "status": "succeeded",
                "created_at": datetime.utcnow() - timedelta(days=30),
                "description": "Premium Mensual"
            }
        ]
    }