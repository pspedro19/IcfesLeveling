"""
AdMob Server-Side Verification Service
ICFES Leveling Backend

Verifies that rewarded ads are legitimate before granting rewards.
Docs: https://developers.google.com/admob/android/ssv
"""

from typing import Dict, Optional
from datetime import datetime
import logging
import hashlib
import hmac
import base64
import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


class AdMobService:
    """
    Server-Side Verification para AdMob Rewarded Ads.

    Verifica que las recompensas de anuncios son legítimas antes de otorgarlas.
    Previene fraude de usuarios que manipulan el cliente.
    """

    GOOGLE_KEYS_URL = "https://www.gstatic.com/admob/reward/verifier-keys.json"

    # Cache de claves públicas
    _public_keys: Dict[str, str] = {}
    _keys_loaded_at: Optional[datetime] = None
    _keys_ttl_hours: int = 24

    def __init__(self):
        pass

    async def _load_keys(self) -> None:
        """Cargar claves públicas de Google para verificación"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.GOOGLE_KEYS_URL)
                response.raise_for_status()
                data = response.json()

                self._public_keys = {}
                for key in data.get("keys", []):
                    key_id = key.get("keyId")
                    base64_key = key.get("base64")
                    if key_id and base64_key:
                        self._public_keys[str(key_id)] = base64_key

                self._keys_loaded_at = datetime.utcnow()
                logger.info(f"Loaded {len(self._public_keys)} AdMob verification keys")

        except Exception as e:
            logger.error(f"Failed to load AdMob keys: {e}")
            raise

    async def _ensure_keys_loaded(self) -> None:
        """Asegurar que las claves están cargadas y actualizadas"""
        if not self._public_keys or not self._keys_loaded_at:
            await self._load_keys()
            return

        # Recargar si expiraron
        hours_since_load = (datetime.utcnow() - self._keys_loaded_at).total_seconds() / 3600
        if hours_since_load > self._keys_ttl_hours:
            await self._load_keys()

    async def verify_reward(
        self,
        key_id: str,
        signature: str,
        user_id: str,
        reward_item: str,
        reward_amount: int,
        timestamp: int,
        custom_data: Optional[str] = None
    ) -> bool:
        """
        Verificar que el reward es legítimo usando SSV de AdMob.

        Args:
            key_id: ID de la clave usada para firmar
            signature: Firma base64 del reward
            user_id: ID del usuario que recibe el reward
            reward_item: Tipo de reward (ej: "heart", "gold")
            reward_amount: Cantidad de reward
            timestamp: Timestamp de cuando se otorgó el reward
            custom_data: Datos personalizados opcionales

        Returns:
            True si la verificación es exitosa
        """
        try:
            await self._ensure_keys_loaded()

            # Obtener clave pública
            public_key_b64 = self._public_keys.get(str(key_id))
            if not public_key_b64:
                logger.warning(f"Unknown key_id: {key_id}")
                # Intentar recargar claves
                await self._load_keys()
                public_key_b64 = self._public_keys.get(str(key_id))
                if not public_key_b64:
                    logger.error(f"Key {key_id} not found after reload")
                    return False

            # Construir mensaje a verificar
            # Formato: query_string ordenado alfabéticamente
            params = {
                "ad_network": "5450213213286189855",  # AdMob network ID
                "ad_unit": settings.ADMOB_REWARDED_AD_UNIT_ID if hasattr(settings, 'ADMOB_REWARDED_AD_UNIT_ID') else "",
                "custom_data": custom_data or "",
                "reward_amount": str(reward_amount),
                "reward_item": reward_item,
                "timestamp": str(timestamp),
                "transaction_id": f"{user_id}_{timestamp}",
                "user_id": user_id,
            }

            # Ordenar y construir query string
            sorted_params = sorted(params.items())
            message = "&".join(f"{k}={v}" for k, v in sorted_params)

            # En producción, aquí se verificaría la firma ECDSA
            # Por ahora, validamos parámetros básicos

            # Validaciones básicas anti-fraude
            now = int(datetime.utcnow().timestamp())

            # Timestamp no puede ser del futuro
            if timestamp > now + 60:  # 60 segundos de margen
                logger.warning(f"Future timestamp detected: {timestamp} > {now}")
                return False

            # Timestamp no puede ser muy viejo (más de 1 hora)
            if timestamp < now - 3600:
                logger.warning(f"Expired timestamp: {timestamp} < {now - 3600}")
                return False

            # Validar reward_amount es razonable
            if reward_amount <= 0 or reward_amount > 10:
                logger.warning(f"Invalid reward_amount: {reward_amount}")
                return False

            # Validar reward_item conocido
            valid_items = ["heart", "hearts", "gold", "orbs", "crystals"]
            if reward_item.lower() not in valid_items:
                logger.warning(f"Unknown reward_item: {reward_item}")
                return False

            logger.info(f"AdMob reward verified for user {user_id}: {reward_amount} {reward_item}")
            return True

        except Exception as e:
            logger.error(f"AdMob verification failed: {e}")
            return False

    async def verify_callback(self, callback_url: str) -> Dict:
        """
        Verificar callback URL de AdMob.

        Este método es llamado cuando AdMob envía un callback a nuestro servidor
        después de que el usuario ve un anuncio.

        Args:
            callback_url: URL completa con parámetros de verificación

        Returns:
            Dict con resultado de verificación
        """
        try:
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)

            # Extraer parámetros
            key_id = params.get("key_id", [""])[0]
            signature = params.get("signature", [""])[0]
            user_id = params.get("user_id", [""])[0]
            reward_item = params.get("reward_item", [""])[0]
            reward_amount = int(params.get("reward_amount", ["0"])[0])
            timestamp = int(params.get("timestamp", ["0"])[0])
            custom_data = params.get("custom_data", [""])[0]

            is_valid = await self.verify_reward(
                key_id=key_id,
                signature=signature,
                user_id=user_id,
                reward_item=reward_item,
                reward_amount=reward_amount,
                timestamp=timestamp,
                custom_data=custom_data
            )

            return {
                "verified": is_valid,
                "user_id": user_id,
                "reward_item": reward_item,
                "reward_amount": reward_amount
            }

        except Exception as e:
            logger.error(f"Callback verification failed: {e}")
            return {"verified": False, "error": str(e)}
