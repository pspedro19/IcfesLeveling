"""
Servicio de integración con Wompi para pagos en Colombia
Wompi es la plataforma de pagos de Bancolombia
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
import httpx
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.user import User
from ..models.subscription import Subscription, Payment, PaymentMethod

logger = logging.getLogger(__name__)

class WompiService:
    """
    Servicio para gestionar pagos con Wompi Colombia
    Documentación: https://docs.wompi.co
    """
    
    def __init__(self):
        # URLs de Wompi
        self.base_url = "https://production.wompi.co/v1" if settings.ENVIRONMENT == "production" else "https://sandbox.wompi.co/v1"
        self.widget_url = "https://checkout.wompi.co/p/" if settings.ENVIRONMENT == "production" else "https://checkout-test.wompi.co/p/"
        
        # Credenciales de Wompi (configurar en .env)
        self.public_key = settings.WOMPI_PUBLIC_KEY
        self.private_key = settings.WOMPI_PRIVATE_KEY
        self.event_secret = settings.WOMPI_EVENT_SECRET
        
        # Configuración de planes
        self.subscription_plans = {
            "basic": {
                "name": "Plan Básico",
                "price_cop": 29900,  # COP mensual
                "features": [
                    "Acceso a todas las materias",
                    "100 preguntas diarias",
                    "Videos ilimitados",
                    "1 simulacro semanal",
                    "Reportes básicos"
                ],
                "duration_days": 30,
                "xp_bonus": 1.0,
                "orbs_monthly": 500
            },
            "premium": {
                "name": "Plan Premium",
                "price_cop": 49900,  # COP mensual
                "features": [
                    "Todo del plan básico",
                    "Preguntas ilimitadas",
                    "Tutorías IA personalizadas",
                    "Simulacros ilimitados",
                    "Análisis predictivo ICFES",
                    "XP doble",
                    "Shadow Army exclusivo",
                    "1000 orbes mensuales"
                ],
                "duration_days": 30,
                "xp_bonus": 2.0,
                "orbs_monthly": 1000
            },
            "elite": {
                "name": "Plan Elite",
                "price_cop": 99900,  # COP trimestral
                "features": [
                    "Todo del plan premium",
                    "Mentoría 1-a-1 semanal",
                    "Acceso anticipado a contenido",
                    "Rango S automático",
                    "XP triple",
                    "Items exclusivos",
                    "2000 orbes mensuales",
                    "Nombre dorado en rankings"
                ],
                "duration_days": 90,
                "xp_bonus": 3.0,
                "orbs_monthly": 2000
            }
        }
        
        # Métodos de pago disponibles en Colombia
        self.payment_methods = {
            "CARD": "Tarjeta de crédito/débito",
            "NEQUI": "Nequi",
            "PSE": "PSE (Transferencia bancaria)",
            "BANCOLOMBIA_TRANSFER": "Transferencia Bancolombia",
            "BANCOLOMBIA_COLLECT": "Corresponsal Bancolombia",
            "EFECTY": "Efecty"
        }
    
    async def create_payment_link(
        self,
        user: User,
        plan_id: str,
        redirect_url: str = None
    ) -> Dict[str, Any]:
        """
        Crear link de pago con Wompi
        """
        if plan_id not in self.subscription_plans:
            raise ValueError(f"Plan inválido: {plan_id}")
        
        plan = self.subscription_plans[plan_id]
        amount_in_cents = plan["price_cop"] * 100  # Wompi requiere centavos
        
        # Crear referencia única
        reference = f"ICFES-{user.id}-{plan_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Generar firma de integridad
        signature = self._generate_signature(reference, amount_in_cents, "COP")
        
        # Crear link de pago
        payload = {
            "name": f"Suscripción {plan['name']} - ICFES Leveling",
            "description": f"Suscripción mensual al {plan['name']} de ICFES Leveling",
            "single_use": False,
            "collect_shipping": False,
            "currency": "COP",
            "amount_in_cents": amount_in_cents,
            "redirect_url": redirect_url or f"{settings.FRONTEND_URL}/payment/success",
            "image_url": f"{settings.FRONTEND_URL}/logo.png",
            "customer_email": user.email,
            "customer_data": {
                "phone_number": user.phone_number,
                "full_name": user.display_name or user.username,
                "legal_id": user.document_number,
                "legal_id_type": user.document_type or "CC"
            },
            "reference": reference,
            "public_key": self.public_key,
            "signature": signature,
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            # Metadata adicional
            "metadata": {
                "user_id": str(user.id),
                "plan_id": plan_id,
                "plan_name": plan["name"],
                "duration_days": plan["duration_days"]
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/links",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.private_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 201:
                    data = response.json()["data"]
                    return {
                        "success": True,
                        "payment_url": f"{self.widget_url}{data['id']}",
                        "link_id": data["id"],
                        "reference": reference,
                        "expires_at": data["expires_at"]
                    }
                else:
                    logger.error(f"Error creando link de pago: {response.text}")
                    return {
                        "success": False,
                        "error": "Error creando link de pago"
                    }
                    
        except Exception as e:
            logger.error(f"Error conectando con Wompi: {str(e)}")
            return {
                "success": False,
                "error": "Error de conexión con pasarela de pago"
            }
    
    async def create_subscription(
        self,
        user: User,
        plan_id: str,
        payment_method: str,
        card_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crear suscripción recurrente con Wompi
        """
        if plan_id not in self.subscription_plans:
            raise ValueError(f"Plan inválido: {plan_id}")
        
        plan = self.subscription_plans[plan_id]
        amount_in_cents = plan["price_cop"] * 100
        
        # Tokenizar tarjeta si es necesario
        if payment_method == "CARD" and not card_token:
            return {
                "success": False,
                "error": "Token de tarjeta requerido"
            }
        
        # Crear plan de suscripción en Wompi
        plan_payload = {
            "name": plan["name"],
            "description": f"Suscripción {plan['name']} ICFES Leveling",
            "amount_in_cents": amount_in_cents,
            "currency": "COP",
            "interval": "month",
            "interval_count": 1,
            "trial_days": 0
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Crear plan
                plan_response = await client.post(
                    f"{self.base_url}/plans",
                    json=plan_payload,
                    headers={
                        "Authorization": f"Bearer {self.private_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if plan_response.status_code != 201:
                    return {
                        "success": False,
                        "error": "Error creando plan de suscripción"
                    }
                
                wompi_plan_id = plan_response.json()["data"]["id"]
                
                # Crear suscripción
                subscription_payload = {
                    "plan_id": wompi_plan_id,
                    "customer_email": user.email,
                    "payment_method": {
                        "type": payment_method,
                        "token": card_token
                    } if payment_method == "CARD" else {
                        "type": payment_method
                    },
                    "customer_data": {
                        "phone_number": user.phone_number,
                        "full_name": user.display_name or user.username,
                        "legal_id": user.document_number,
                        "legal_id_type": user.document_type or "CC"
                    },
                    "reference": f"SUB-{user.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                }
                
                sub_response = await client.post(
                    f"{self.base_url}/subscriptions",
                    json=subscription_payload,
                    headers={
                        "Authorization": f"Bearer {self.private_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if sub_response.status_code == 201:
                    data = sub_response.json()["data"]
                    return {
                        "success": True,
                        "subscription_id": data["id"],
                        "status": data["status"],
                        "next_payment_date": data["next_payment_date"]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Error creando suscripción"
                    }
                    
        except Exception as e:
            logger.error(f"Error creando suscripción: {str(e)}")
            return {
                "success": False,
                "error": "Error procesando suscripción"
            }
    
    async def process_webhook(
        self,
        event_type: str,
        data: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Procesar webhook de Wompi
        """
        # Verificar firma del webhook
        if not self._verify_webhook_signature(data, signature):
            logger.warning("Firma de webhook inválida")
            return False
        
        try:
            if event_type == "transaction.updated":
                await self._handle_transaction_update(data)
            elif event_type == "subscription.created":
                await self._handle_subscription_created(data)
            elif event_type == "subscription.cancelled":
                await self._handle_subscription_cancelled(data)
            elif event_type == "subscription.payment.success":
                await self._handle_subscription_payment(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
            return False
    
    async def _handle_transaction_update(self, data: Dict[str, Any]):
        """
        Manejar actualización de transacción
        """
        transaction = data["transaction"]
        reference = transaction["reference"]
        status = transaction["status"]
        
        # Extraer información de la referencia
        parts = reference.split("-")
        if len(parts) >= 3:
            user_id = parts[1]
            plan_id = parts[2]
            
            if status == "APPROVED":
                # Activar suscripción
                await self._activate_subscription(user_id, plan_id, transaction)
            elif status == "DECLINED" or status == "ERROR":
                # Notificar fallo de pago
                await self._notify_payment_failure(user_id, transaction)
    
    async def _activate_subscription(
        self,
        user_id: str,
        plan_id: str,
        transaction: Dict[str, Any]
    ):
        """
        Activar suscripción después de pago exitoso
        """
        from ..core.database import SessionLocal
        
        db = SessionLocal()
        try:
            # Buscar usuario
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            plan = self.subscription_plans[plan_id]
            
            # Crear o actualizar suscripción
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()
            
            if not subscription:
                subscription = Subscription(
                    user_id=user_id,
                    plan_id=plan_id,
                    plan_name=plan["name"],
                    status="active",
                    start_date=datetime.now(),
                    end_date=datetime.now() + timedelta(days=plan["duration_days"]),
                    price=Decimal(str(plan["price_cop"])),
                    wompi_subscription_id=transaction.get("subscription_id"),
                    features=plan["features"],
                    xp_multiplier=plan["xp_bonus"],
                    monthly_orbs=plan["orbs_monthly"]
                )
                db.add(subscription)
            else:
                subscription.status = "active"
                subscription.plan_id = plan_id
                subscription.plan_name = plan["name"]
                subscription.end_date = datetime.now() + timedelta(days=plan["duration_days"])
                subscription.xp_multiplier = plan["xp_bonus"]
                subscription.monthly_orbs = plan["orbs_monthly"]
            
            # Registrar pago
            payment = Payment(
                user_id=user_id,
                subscription_id=subscription.id if subscription.id else None,
                amount=Decimal(str(plan["price_cop"])),
                currency="COP",
                status="completed",
                payment_method=transaction.get("payment_method_type", "UNKNOWN"),
                wompi_transaction_id=transaction["id"],
                reference=transaction["reference"],
                paid_at=datetime.now()
            )
            db.add(payment)
            
            # Actualizar usuario a premium
            user.premium_plan = plan_id
            user.premium_until = datetime.now() + timedelta(days=plan["duration_days"])
            
            # Otorgar beneficios inmediatos
            user.orbs += plan["orbs_monthly"]
            if plan_id == "elite":
                user.rank = "S"
                user.shadow_slots = 10
            elif plan_id == "premium":
                user.shadow_slots = 5
            
            db.commit()
            
            # Enviar notificación al usuario
            await self._send_subscription_notification(user, plan)
            
        except Exception as e:
            logger.error(f"Error activando suscripción: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def _generate_signature(
        self,
        reference: str,
        amount_in_cents: int,
        currency: str
    ) -> str:
        """
        Generar firma de integridad para Wompi
        """
        message = f"{reference}{amount_in_cents}{currency}{self.event_secret}"
        signature = hashlib.sha256(message.encode()).hexdigest()
        return signature
    
    def _verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Verificar firma de webhook
        """
        # Reconstruir payload como string
        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        
        # Calcular firma esperada
        expected_signature = hmac.new(
            self.event_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def _send_subscription_notification(
        self,
        user: User,
        plan: Dict[str, Any]
    ):
        """
        Enviar notificación de suscripción activada
        """
        from ..services.notification_service import notification_service
        
        notification_service.send_custom(
            user_id=user.id,
            title="¡Suscripción Activada!",
            body=f"Tu {plan['name']} está activo. ¡Disfruta de todos los beneficios!",
            data={
                "plan_name": plan["name"],
                "xp_bonus": str(plan["xp_bonus"]),
                "orbs_received": str(plan["orbs_monthly"])
            }
        )
    
    async def _notify_payment_failure(
        self,
        user_id: str,
        transaction: Dict[str, Any]
    ):
        """
        Notificar fallo de pago
        """
        from ..services.notification_service import notification_service
        
        notification_service.send_custom(
            user_id=user_id,
            title="Pago No Procesado",
            body="Tu pago no pudo ser procesado. Por favor intenta nuevamente.",
            data={
                "reason": transaction.get("failure_message", "Error desconocido"),
                "transaction_id": transaction["id"]
            }
        )
    
    async def cancel_subscription(
        self,
        user_id: str,
        subscription_id: str
    ) -> bool:
        """
        Cancelar suscripción
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/subscriptions/{subscription_id}",
                    headers={
                        "Authorization": f"Bearer {self.private_key}"
                    }
                )
                
                if response.status_code == 200:
                    # Actualizar en base de datos
                    from ..core.database import SessionLocal
                    db = SessionLocal()
                    
                    subscription = db.query(Subscription).filter(
                        Subscription.user_id == user_id,
                        Subscription.wompi_subscription_id == subscription_id
                    ).first()
                    
                    if subscription:
                        subscription.status = "cancelled"
                        subscription.cancelled_at = datetime.now()
                        db.commit()
                    
                    db.close()
                    return True
                    
        except Exception as e:
            logger.error(f"Error cancelando suscripción: {str(e)}")
        
        return False
    
    async def get_payment_methods(self) -> List[Dict[str, Any]]:
        """
        Obtener métodos de pago disponibles
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/merchants/{self.public_key}",
                    headers={
                        "Authorization": f"Bearer {self.public_key}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()["data"]
                    return data.get("payment_methods", [])
                    
        except Exception as e:
            logger.error(f"Error obteniendo métodos de pago: {str(e)}")
        
        return []

# Instancia global del servicio
wompi_service = WompiService()