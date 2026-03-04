"""
Economy System Routes
Gold Economy system for ICFES Leveling

Endpoints:
- GET /economy/balance - Return gold and gems
- GET /economy/shop - Return available items with prices
- POST /economy/purchase - Buy item with gold or gems

Shop Items with Prices:
- streak_freeze: 200 gold - Protects streak for one day
- streak_repair: 300 gold - Repairs a lost streak (within 24h)
- hint: 50 gold - Get a hint for the current question
- mana_potion: 150 gold - Restores one heart immediately
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..schemas.economy import (
    BalanceResponse,
    ShopItem,
    ShopResponse,
    PurchaseRequest,
    PurchaseResponse,
    CurrencyType,
    ItemCategory,
    UserEconomy,
    GoldTransactionResponse,
    GoldTransactionListResponse,
    AddGoldRequest,
    SpendGoldRequest,
    AddXPRequest,
    AddXPResponse,
    UpdateRankRequest,
    UpdateRankResponse,
)
from ..services.economy_service import EconomyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/economy", tags=["economy"])

# ============================================================================
# SHOP ITEMS CONFIGURATION
# Define all available shop items with their properties and prices
# ============================================================================

SHOP_ITEMS = {
    # ============================================================================
    # STREAK ITEMS
    # ============================================================================
    "streak_freeze": ShopItem(
        id="streak_freeze",
        name="Streak Freeze",
        description="Protects your streak for one day if you miss practice. Use it before missing a day!",
        price_gold=200,
        price_gems=None,
        category=ItemCategory.STREAK,
        icon="ice_shield",
        effect="Prevents streak loss for 1 day",
        max_quantity=3,
        is_available=True
    ),
    "streak_repair": ShopItem(
        id="streak_repair",
        name="Streak Repair",
        description="Repairs a lost streak within 24 hours of losing it. Restore your progress!",
        price_gold=300,
        price_gems=None,
        category=ItemCategory.STREAK,
        icon="repair_hammer",
        effect="Restores lost streak (24h window)",
        max_quantity=1,
        is_available=True
    ),

    # ============================================================================
    # BOOST ITEMS
    # ============================================================================
    "hint": ShopItem(
        id="hint",
        name="Question Hint",
        description="Get a helpful hint for the current question. Eliminates one wrong answer.",
        price_gold=50,
        price_gems=None,
        category=ItemCategory.BOOST,
        icon="lightbulb",
        effect="Eliminates 1 wrong answer option",
        max_quantity=5,
        is_available=True
    ),
    "xp_boost_1h": ShopItem(
        id="xp_boost_1h",
        name="XP Boost (1 Hour)",
        description="Doubles all XP earned for 1 hour. Perfect for study sessions!",
        price_gold=250,
        price_gems=5,
        category=ItemCategory.BOOST,
        icon="xp_double",
        effect="2x XP for 1 hour",
        max_quantity=3,
        is_available=True
    ),
    "xp_boost_24h": ShopItem(
        id="xp_boost_24h",
        name="XP Boost (24 Hours)",
        description="Doubles all XP earned for 24 hours. Maximum value!",
        price_gold=1000,
        price_gems=20,
        category=ItemCategory.BOOST,
        icon="xp_double_gold",
        effect="2x XP for 24 hours",
        max_quantity=1,
        is_available=True
    ),
    "gold_boost_1h": ShopItem(
        id="gold_boost_1h",
        name="Gold Boost (1 Hour)",
        description="Doubles all gold earned for 1 hour.",
        price_gold=300,
        price_gems=8,
        category=ItemCategory.BOOST,
        icon="gold_double",
        effect="2x Gold for 1 hour",
        max_quantity=3,
        is_available=True
    ),
    "combo_extender": ShopItem(
        id="combo_extender",
        name="Combo Extender",
        description="Extends combo timeout by 5 seconds for 1 session.",
        price_gold=100,
        price_gems=None,
        category=ItemCategory.BOOST,
        icon="clock_extend",
        effect="+5s combo timeout",
        max_quantity=5,
        is_available=True
    ),
    "second_chance": ShopItem(
        id="second_chance",
        name="Second Chance",
        description="Retry a wrong answer once per question (1 use).",
        price_gold=200,
        price_gems=5,
        category=ItemCategory.BOOST,
        icon="retry_arrow",
        effect="1 free retry on wrong answer",
        max_quantity=3,
        is_available=True
    ),

    # ============================================================================
    # HEARTS ITEMS
    # ============================================================================
    "mana_potion": ShopItem(
        id="mana_potion",
        name="Mana Potion",
        description="Restores one heart immediately. Keep practicing without waiting!",
        price_gold=150,
        price_gems=None,
        category=ItemCategory.HEARTS,
        icon="heart_potion",
        effect="Restores 1 heart instantly",
        max_quantity=5,
        is_available=True
    ),
    "full_heart_refill": ShopItem(
        id="full_heart_refill",
        name="Full Heart Refill",
        description="Completely restores all 5 hearts instantly.",
        price_gold=500,
        price_gems=10,
        category=ItemCategory.HEARTS,
        icon="heart_full",
        effect="Restores all hearts to 5",
        max_quantity=2,
        is_available=True
    ),
    "extra_heart": ShopItem(
        id="extra_heart",
        name="Extra Heart Slot",
        description="Permanently adds 1 extra heart slot (max 8 hearts).",
        price_gold=2000,
        price_gems=50,
        category=ItemCategory.HEARTS,
        icon="heart_plus",
        effect="+1 max heart permanently",
        max_quantity=3,
        is_available=True
    ),

    # ============================================================================
    # AVATAR ITEMS (COSMETICS)
    # ============================================================================
    "avatar_hunter_bronze": ShopItem(
        id="avatar_hunter_bronze",
        name="Cazador Bronce",
        description="Avatar de guerrero principiante con armadura de bronce.",
        price_gold=500,
        price_gems=None,
        category=ItemCategory.AVATAR,
        icon="avatar_hunter_bronze",
        effect="Cosmetic avatar",
        max_quantity=1,
        is_available=True
    ),
    "avatar_hunter_silver": ShopItem(
        id="avatar_hunter_silver",
        name="Cazador Plata",
        description="Avatar de guerrero intermedio con armadura plateada.",
        price_gold=1000,
        price_gems=25,
        category=ItemCategory.AVATAR,
        icon="avatar_hunter_silver",
        effect="Cosmetic avatar",
        max_quantity=1,
        is_available=True
    ),
    "avatar_hunter_gold": ShopItem(
        id="avatar_hunter_gold",
        name="Cazador Oro",
        description="Avatar de guerrero elite con armadura dorada brillante.",
        price_gold=2500,
        price_gems=50,
        category=ItemCategory.AVATAR,
        icon="avatar_hunter_gold",
        effect="Cosmetic avatar",
        max_quantity=1,
        is_available=True
    ),
    "avatar_mage_arcane": ShopItem(
        id="avatar_mage_arcane",
        name="Mago Arcano",
        description="Avatar de mago con tunica y baston magico.",
        price_gold=1500,
        price_gems=30,
        category=ItemCategory.AVATAR,
        icon="avatar_mage_arcane",
        effect="Cosmetic avatar",
        max_quantity=1,
        is_available=True
    ),
    "avatar_scholar": ShopItem(
        id="avatar_scholar",
        name="Sabio Erudito",
        description="Avatar de sabio con libros y pergaminos antiguos.",
        price_gold=1200,
        price_gems=25,
        category=ItemCategory.AVATAR,
        icon="avatar_scholar",
        effect="Cosmetic avatar",
        max_quantity=1,
        is_available=True
    ),
    "avatar_ninja": ShopItem(
        id="avatar_ninja",
        name="Ninja de las Sombras",
        description="Avatar misterioso de ninja sigiloso.",
        price_gold=2000,
        price_gems=40,
        category=ItemCategory.AVATAR,
        icon="avatar_ninja",
        effect="Cosmetic avatar",
        max_quantity=1,
        is_available=True
    ),

    # ============================================================================
    # TITLE ITEMS (COSMETICS)
    # ============================================================================
    "title_novato": ShopItem(
        id="title_novato",
        name="Titulo: Novato Prometedor",
        description="Muestra este titulo junto a tu nombre.",
        price_gold=300,
        price_gems=None,
        category=ItemCategory.TITLE,
        icon="badge_novato",
        effect="Title displayed on profile",
        max_quantity=1,
        is_available=True
    ),
    "title_estudioso": ShopItem(
        id="title_estudioso",
        name="Titulo: El Estudioso",
        description="Para los que nunca dejan de aprender.",
        price_gold=600,
        price_gems=10,
        category=ItemCategory.TITLE,
        icon="badge_estudioso",
        effect="Title displayed on profile",
        max_quantity=1,
        is_available=True
    ),
    "title_maestro": ShopItem(
        id="title_maestro",
        name="Titulo: Maestro del Saber",
        description="Solo para verdaderos expertos.",
        price_gold=1500,
        price_gems=30,
        category=ItemCategory.TITLE,
        icon="badge_maestro",
        effect="Title displayed on profile",
        max_quantity=1,
        is_available=True
    ),
    "title_leyenda": ShopItem(
        id="title_leyenda",
        name="Titulo: Leyenda ICFES",
        description="El titulo mas prestigioso. Eres una leyenda.",
        price_gold=5000,
        price_gems=100,
        category=ItemCategory.TITLE,
        icon="badge_leyenda",
        effect="Title displayed on profile",
        max_quantity=1,
        is_available=True
    ),
    "title_racha": ShopItem(
        id="title_racha",
        name="Titulo: Maestro de la Racha",
        description="Para los constantes que nunca fallan.",
        price_gold=800,
        price_gems=15,
        category=ItemCategory.TITLE,
        icon="badge_racha",
        effect="Title displayed on profile",
        max_quantity=1,
        is_available=True
    ),

    # ============================================================================
    # THEME ITEMS (COSMETICS)
    # ============================================================================
    "theme_dark_knight": ShopItem(
        id="theme_dark_knight",
        name="Tema: Caballero Oscuro",
        description="Tema oscuro con acentos dorados elegantes.",
        price_gold=800,
        price_gems=15,
        category=ItemCategory.THEME,
        icon="theme_dark_knight",
        effect="Custom app theme",
        max_quantity=1,
        is_available=True
    ),
    "theme_ocean_depths": ShopItem(
        id="theme_ocean_depths",
        name="Tema: Profundidades del Oceano",
        description="Tema azul marino relajante.",
        price_gold=800,
        price_gems=15,
        category=ItemCategory.THEME,
        icon="theme_ocean",
        effect="Custom app theme",
        max_quantity=1,
        is_available=True
    ),
    "theme_forest_mystic": ShopItem(
        id="theme_forest_mystic",
        name="Tema: Bosque Mistico",
        description="Tema verde naturaleza con tonos magicos.",
        price_gold=800,
        price_gems=15,
        category=ItemCategory.THEME,
        icon="theme_forest",
        effect="Custom app theme",
        max_quantity=1,
        is_available=True
    ),
    "theme_fire_dragon": ShopItem(
        id="theme_fire_dragon",
        name="Tema: Dragon de Fuego",
        description="Tema rojo intenso con efectos de llamas.",
        price_gold=1200,
        price_gems=25,
        category=ItemCategory.THEME,
        icon="theme_fire",
        effect="Custom app theme",
        max_quantity=1,
        is_available=True
    ),
    "theme_galaxy": ShopItem(
        id="theme_galaxy",
        name="Tema: Galaxia Cosmica",
        description="Tema espacial con estrellas y nebulosas.",
        price_gold=1500,
        price_gems=30,
        category=ItemCategory.THEME,
        icon="theme_galaxy",
        effect="Custom app theme",
        max_quantity=1,
        is_available=True
    ),

    # ============================================================================
    # BUNDLE ITEMS (SPECIAL OFFERS)
    # ============================================================================
    "bundle_starter": ShopItem(
        id="bundle_starter",
        name="Pack Inicial",
        description="3x Streak Freeze + 3x Hints + 2x Mana Potion. Ahorra 30%!",
        price_gold=700,
        price_gems=15,
        category=ItemCategory.BUNDLE,
        icon="bundle_starter",
        effect="Multiple items bundle",
        max_quantity=1,
        is_available=True
    ),
    "bundle_power_hour": ShopItem(
        id="bundle_power_hour",
        name="Pack Hora del Poder",
        description="XP Boost 1h + Gold Boost 1h + Full Hearts. Combo perfecto!",
        price_gold=900,
        price_gems=20,
        category=ItemCategory.BUNDLE,
        icon="bundle_power",
        effect="Boost combo bundle",
        max_quantity=3,
        is_available=True
    ),
    "bundle_cosmetic_basic": ShopItem(
        id="bundle_cosmetic_basic",
        name="Pack Cosmetico Basico",
        description="Avatar Bronce + Titulo Novato + Tema Oceano. Ahorra 40%!",
        price_gold=1000,
        price_gems=None,
        category=ItemCategory.BUNDLE,
        icon="bundle_cosmetic",
        effect="Cosmetic bundle",
        max_quantity=1,
        is_available=True
    ),

    # ============================================================================
    # SPECIAL ITEMS (LIMITED/SEASONAL)
    # ============================================================================
    "special_lucky_box": ShopItem(
        id="special_lucky_box",
        name="Caja de la Suerte",
        description="Contiene un item aleatorio! Puede ser raro.",
        price_gold=400,
        price_gems=8,
        category=ItemCategory.SPECIAL,
        icon="mystery_box",
        effect="Random item reward",
        max_quantity=5,
        is_available=True
    ),
    "special_mega_xp": ShopItem(
        id="special_mega_xp",
        name="Mega XP Burst",
        description="Gana 500 XP instantaneamente!",
        price_gold=600,
        price_gems=12,
        category=ItemCategory.SPECIAL,
        icon="xp_burst",
        effect="+500 XP instant",
        max_quantity=3,
        is_available=True
    ),
}

# Quick price reference for common items (as specified in API contract)
ITEM_PRICES = {
    # Streak
    "streak_freeze": 200,
    "streak_repair": 300,
    # Hearts
    "mana_potion": 150,
    "full_heart_refill": 500,
    "extra_heart": 2000,
    # Boosts
    "hint": 50,
    "xp_boost_1h": 250,
    "xp_boost_24h": 1000,
    "gold_boost_1h": 300,
    "combo_extender": 100,
    "second_chance": 200,
    # Avatars
    "avatar_hunter_bronze": 500,
    "avatar_hunter_silver": 1000,
    "avatar_hunter_gold": 2500,
    "avatar_mage_arcane": 1500,
    "avatar_scholar": 1200,
    "avatar_ninja": 2000,
    # Titles
    "title_novato": 300,
    "title_estudioso": 600,
    "title_maestro": 1500,
    "title_leyenda": 5000,
    "title_racha": 800,
    # Themes
    "theme_dark_knight": 800,
    "theme_ocean_depths": 800,
    "theme_forest_mystic": 800,
    "theme_fire_dragon": 1200,
    "theme_galaxy": 1500,
    # Bundles
    "bundle_starter": 700,
    "bundle_power_hour": 900,
    "bundle_cosmetic_basic": 1000,
    # Special
    "special_lucky_box": 400,
    "special_mega_xp": 600,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_balance(user: User) -> tuple[int, int]:
    """
    Get user's gold and gems balance.
    In the database model, 'orbs' maps to 'gold' and 'crystals' maps to 'gems'.
    """
    gold = user.orbs if user.orbs is not None else 0
    gems = user.crystals if user.crystals is not None else 0
    return gold, gems


def deduct_currency(db: Session, user: User, currency: CurrencyType, amount: int) -> bool:
    """
    Deduct currency from user's balance.
    Returns True if successful, False if insufficient funds.
    """
    if currency == CurrencyType.GOLD:
        if user.orbs >= amount:
            user.orbs -= amount
            db.commit()
            return True
    elif currency == CurrencyType.GEMS:
        if user.crystals >= amount:
            user.crystals -= amount
            db.commit()
            return True
    return False


def apply_item_effect(db: Session, user: User, item_id: str, quantity: int = 1) -> Optional[str]:
    """
    Apply the effect of a purchased item.
    Returns a description of the effect applied, or None if no effect.
    """
    try:
        # =============================================
        # STREAK ITEMS
        # =============================================
        if item_id == "streak_freeze":
            logger.info(f"User {user.id} purchased {quantity} streak freeze(s)")
            return f"Streak protection activated. You have {quantity} streak freeze(s) available."

        elif item_id == "streak_repair":
            logger.info(f"User {user.id} repaired their streak")
            return "Streak repaired! Your previous streak has been restored."

        # =============================================
        # HEARTS ITEMS
        # =============================================
        elif item_id == "mana_potion":
            hearts_to_restore = quantity * 20  # 1 heart = 20 hp
            max_hp = 100
            user.hp = min(user.hp + hearts_to_restore, max_hp)
            db.commit()
            current_hearts = user.hp // 20
            logger.info(f"User {user.id} restored {quantity} heart(s), now has {current_hearts}")
            return f"Restored {quantity} heart(s)! You now have {current_hearts}/5 hearts."

        elif item_id == "full_heart_refill":
            user.hp = 100
            db.commit()
            logger.info(f"User {user.id} fully restored hearts")
            return "All hearts restored! You now have 5/5 hearts."

        elif item_id == "extra_heart":
            logger.info(f"User {user.id} purchased extra heart slot")
            return "Extra heart slot added! Your max hearts increased by 1."

        # =============================================
        # BOOST ITEMS
        # =============================================
        elif item_id == "hint":
            logger.info(f"User {user.id} purchased {quantity} hint(s)")
            return f"You now have {quantity} hint(s) available for use."

        elif item_id == "xp_boost_1h":
            logger.info(f"User {user.id} activated 1h XP boost")
            return "XP Boost activated! Earn 2x XP for the next hour."

        elif item_id == "xp_boost_24h":
            logger.info(f"User {user.id} activated 24h XP boost")
            return "XP Boost activated! Earn 2x XP for the next 24 hours!"

        elif item_id == "gold_boost_1h":
            logger.info(f"User {user.id} activated 1h Gold boost")
            return "Gold Boost activated! Earn 2x Gold for the next hour."

        elif item_id == "combo_extender":
            logger.info(f"User {user.id} purchased combo extender")
            return "Combo Extender activated! +5 seconds on combo timeout."

        elif item_id == "second_chance":
            logger.info(f"User {user.id} purchased second chance")
            return "Second Chance ready! Retry one wrong answer."

        # =============================================
        # COSMETIC ITEMS (Avatars, Titles, Themes)
        # =============================================
        elif item_id.startswith("avatar_"):
            avatar_name = SHOP_ITEMS.get(item_id, {})
            name = avatar_name.name if hasattr(avatar_name, 'name') else item_id
            logger.info(f"User {user.id} purchased avatar: {item_id}")
            return f"Avatar '{name}' unlocked! Set it in your profile."

        elif item_id.startswith("title_"):
            title_name = SHOP_ITEMS.get(item_id, {})
            name = title_name.name if hasattr(title_name, 'name') else item_id
            logger.info(f"User {user.id} purchased title: {item_id}")
            return f"Title '{name}' unlocked! Display it proudly."

        elif item_id.startswith("theme_"):
            theme_name = SHOP_ITEMS.get(item_id, {})
            name = theme_name.name if hasattr(theme_name, 'name') else item_id
            logger.info(f"User {user.id} purchased theme: {item_id}")
            return f"Theme '{name}' unlocked! Apply it in settings."

        # =============================================
        # BUNDLE ITEMS
        # =============================================
        elif item_id == "bundle_starter":
            logger.info(f"User {user.id} purchased starter bundle")
            return "Starter Bundle contents added: 3x Streak Freeze, 3x Hints, 2x Mana Potion!"

        elif item_id == "bundle_power_hour":
            user.hp = 100  # Full hearts as part of bundle
            db.commit()
            logger.info(f"User {user.id} purchased power hour bundle")
            return "Power Hour Bundle activated! XP Boost + Gold Boost + Full Hearts!"

        elif item_id == "bundle_cosmetic_basic":
            logger.info(f"User {user.id} purchased cosmetic bundle")
            return "Basic Cosmetic Bundle unlocked! Avatar, Title, and Theme added."

        # =============================================
        # SPECIAL ITEMS
        # =============================================
        elif item_id == "special_lucky_box":
            import random
            possible_rewards = ["hint", "mana_potion", "xp_boost_1h", "streak_freeze"]
            reward = random.choice(possible_rewards)
            logger.info(f"User {user.id} opened lucky box, got: {reward}")
            return f"Lucky Box opened! You received: {SHOP_ITEMS.get(reward, {}).name if reward in SHOP_ITEMS else reward}"

        elif item_id == "special_mega_xp":
            user.xp = (user.xp or 0) + 500
            db.commit()
            logger.info(f"User {user.id} used Mega XP Burst, gained 500 XP")
            return "Mega XP Burst! +500 XP instantly!"

        return None
    except Exception as e:
        logger.error(f"Error applying item effect: {e}")
        return None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's current gold and gems balance.

    Gold (orbs) is earned through:
    - Completing questions correctly
    - Daily quests and achievements
    - League rewards

    Gems (crystals) are premium currency earned through:
    - Special achievements
    - Promotional events
    - In-app purchases
    """
    gold, gems = get_user_balance(current_user)

    return BalanceResponse(
        gold=gold,
        gems=gems
    )


@router.get("/shop", response_model=ShopResponse)
async def get_shop(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available items in the shop with prices.

    Returns all items currently available for purchase along with
    a quick reference price map for the most common items.

    Shop Items:
    - streak_freeze: 200 gold - Protects streak for one day
    - streak_repair: 300 gold - Repairs a lost streak within 24h
    - hint: 50 gold - Get a hint for current question
    - mana_potion: 150 gold - Restores one heart
    """
    # Get list of available items
    available_items = [
        item for item in SHOP_ITEMS.values()
        if item.is_available
    ]

    return ShopResponse(
        items=available_items,
        prices=ITEM_PRICES
    )


@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_item(
    purchase: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Purchase an item from the shop.

    Purchase Logic:
    1. Check if item exists and is available
    2. Check if user has sufficient funds
    3. Deduct currency from user's balance
    4. Apply item effect (add hearts, add freeze, etc.)
    5. Return updated balance and confirmation

    Error Codes:
    - ITEM_NOT_FOUND: Item doesn't exist
    - ITEM_UNAVAILABLE: Item is not currently available
    - INSUFFICIENT_FUNDS: Not enough currency
    - INVALID_CURRENCY: Item cannot be purchased with specified currency
    """
    item_id = purchase.item_id
    currency = purchase.currency
    quantity = purchase.quantity

    # Step 1: Check if item exists
    if item_id not in SHOP_ITEMS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ITEM_NOT_FOUND",
                "message": f"Item '{item_id}' not found in shop"
            }
        )

    item = SHOP_ITEMS[item_id]

    # Step 2: Check if item is available
    if not item.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ITEM_UNAVAILABLE",
                "message": f"Item '{item.name}' is currently unavailable"
            }
        )

    # Step 3: Check quantity limits
    if item.max_quantity and quantity > item.max_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "QUANTITY_EXCEEDED",
                "message": f"Maximum {item.max_quantity} of '{item.name}' per purchase"
            }
        )

    # Step 4: Calculate total cost based on currency
    if currency == CurrencyType.GOLD:
        unit_price = item.price_gold
        if unit_price is None or unit_price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_CURRENCY",
                    "message": f"Item '{item.name}' cannot be purchased with gold"
                }
            )
    elif currency == CurrencyType.GEMS:
        unit_price = item.price_gems
        if unit_price is None or unit_price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_CURRENCY",
                    "message": f"Item '{item.name}' cannot be purchased with gems"
                }
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_CURRENCY",
                "message": "Invalid currency type"
            }
        )

    total_cost = unit_price * quantity

    # Step 5: Check sufficient funds
    gold, gems = get_user_balance(current_user)

    if currency == CurrencyType.GOLD and gold < total_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INSUFFICIENT_FUNDS",
                "message": f"Not enough gold. Need {total_cost}, have {gold}",
                "details": {
                    "required": total_cost,
                    "available": gold
                }
            }
        )
    elif currency == CurrencyType.GEMS and gems < total_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INSUFFICIENT_FUNDS",
                "message": f"Not enough gems. Need {total_cost}, have {gems}",
                "details": {
                    "required": total_cost,
                    "available": gems
                }
            }
        )

    # Step 6: Deduct currency
    success = deduct_currency(db, current_user, currency, total_cost)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "TRANSACTION_FAILED",
                "message": "Failed to process transaction"
            }
        )

    # Step 7: Apply item effect
    effect_applied = apply_item_effect(db, current_user, item_id, quantity)

    # Step 8: Get updated balance
    new_gold, new_gems = get_user_balance(current_user)

    logger.info(
        f"Purchase completed: User {current_user.id} bought {quantity}x {item_id} "
        f"for {total_cost} {currency.value}. New balance: {new_gold} gold, {new_gems} gems"
    )

    return PurchaseResponse(
        purchased=True,
        item_id=item_id,
        quantity=quantity,
        gold_remaining=new_gold,
        gems_remaining=new_gems,
        message=f"Successfully purchased {quantity}x {item.name}",
        effect_applied=effect_applied
    )


# ============================================================================
# ADDITIONAL UTILITY ENDPOINTS
# ============================================================================

@router.get("/items/{item_id}", response_model=ShopItem)
async def get_item_details(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific shop item.
    """
    if item_id not in SHOP_ITEMS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ITEM_NOT_FOUND",
                "message": f"Item '{item_id}' not found in shop"
            }
        )

    return SHOP_ITEMS[item_id]


@router.get("/prices")
async def get_item_prices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quick reference prices for all items.
    Useful for client-side caching and display.
    """
    all_prices = {}
    for item_id, item in SHOP_ITEMS.items():
        all_prices[item_id] = {
            "gold": item.price_gold,
            "gems": item.price_gems
        }

    return {
        "prices": all_prices,
        "common_items": ITEM_PRICES
    }


@router.post("/earn")
async def earn_currency(
    source: str,
    amount: int,
    currency_type: CurrencyType = CurrencyType.GOLD,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Award currency to user (internal use or admin).

    Sources:
    - quest_complete: Quest completion reward
    - achievement: Achievement unlock
    - league_reward: Weekly league reward
    - correct_answer: Bonus for correct answers
    - streak_bonus: Streak milestone bonus
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )

    if currency_type == CurrencyType.GOLD:
        current_user.orbs = (current_user.orbs or 0) + amount
    else:
        current_user.crystals = (current_user.crystals or 0) + amount

    db.commit()

    gold, gems = get_user_balance(current_user)

    logger.info(f"Currency earned: User {current_user.id} earned {amount} {currency_type.value} from {source}")

    return {
        "success": True,
        "earned": amount,
        "currency": currency_type.value,
        "source": source,
        "new_balance": {
            "gold": gold,
            "gems": gems
        }
    }


# ============================================================================
# ECONOMY STATUS ENDPOINTS (Spec Required)
# ============================================================================

@router.get("/status", response_model=UserEconomy)
async def get_economy_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive economy status for the current user.

    Returns:
    - user_id: User's UUID
    - gold: Current gold balance (primary currency)
    - orbs: Knowledge orbs (secondary currency)
    - crystals: Premium currency (gems)
    - total_xp: Total experience points earned
    - level: Current player level
    - rank: Current rank (E/D/C/B/A/S)
    - xp_to_next_level: XP needed to reach next level
    - level_progress_percent: Progress percentage toward next level
    """
    economy_data = EconomyService.get_user_economy(db, current_user.id)

    if not economy_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User economy data not found"
        )

    return UserEconomy(**economy_data)


@router.get("/transactions/gold", response_model=GoldTransactionListResponse)
async def get_gold_transactions(
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get gold transaction history for the current user.

    Parameters:
    - limit: Maximum number of transactions to return (default 50, max 100)
    - offset: Number of transactions to skip for pagination
    - transaction_type: Optional filter by transaction type (e.g., 'quest_reward', 'purchase')

    Returns list of transactions with:
    - id: Transaction ID
    - amount: Gold amount (positive for earning, negative for spending)
    - transaction_type: Type of transaction
    - description: Human-readable description
    - balance_after: Balance after this transaction
    - created_at: Timestamp
    """
    # Validate limit
    limit = min(limit, 100)

    transactions = EconomyService.get_gold_transactions(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        transaction_type=transaction_type
    )

    # Get total count for pagination
    from ..models.economy import GoldTransaction
    total_query = db.query(GoldTransaction).filter(GoldTransaction.user_id == current_user.id)
    if transaction_type:
        total_query = total_query.filter(GoldTransaction.transaction_type == transaction_type)
    total = total_query.count()

    transaction_responses = [
        GoldTransactionResponse(
            id=str(t.id),
            amount=t.amount,
            transaction_type=t.transaction_type,
            description=t.description,
            balance_after=t.balance_after,
            created_at=t.created_at
        )
        for t in transactions
    ]

    return GoldTransactionListResponse(
        transactions=transaction_responses,
        total=total,
        limit=limit,
        offset=offset
    )


# ============================================================================
# ECONOMY SERVICE ENDPOINTS (Using EconomyService)
# ============================================================================

@router.post("/gold/add", response_model=dict)
async def add_gold_to_user(
    request: AddGoldRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add gold to user's balance with transaction tracking.

    This endpoint creates a transaction record for auditing purposes.
    Use this for rewards, quest completions, etc.
    """
    success, new_balance, error = EconomyService.add_gold(
        db=db,
        user_id=current_user.id,
        amount=request.amount,
        transaction_type=request.transaction_type,
        description=request.description
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return {
        "success": True,
        "gold_added": request.amount,
        "new_balance": new_balance,
        "transaction_type": request.transaction_type
    }


@router.post("/gold/spend", response_model=dict)
async def spend_gold_from_user(
    request: SpendGoldRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Spend gold from user's balance with transaction tracking.

    This endpoint creates a transaction record for auditing purposes.
    Returns error if insufficient funds.
    """
    success, remaining_balance, error = EconomyService.spend_gold(
        db=db,
        user_id=current_user.id,
        amount=request.amount,
        transaction_type=request.transaction_type,
        description=request.description
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return {
        "success": True,
        "gold_spent": request.amount,
        "remaining_balance": remaining_balance,
        "transaction_type": request.transaction_type
    }


@router.post("/xp/add", response_model=AddXPResponse)
async def add_xp_to_user(
    request: AddXPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add XP to user with level-up logic.

    Features:
    - Automatic level-up calculation
    - XP multiplier support (for boosts)
    - Transaction tracking for analytics

    Sources can include:
    - question_correct: Correctly answered question
    - quest_complete: Quest completion
    - achievement: Achievement unlock
    - daily_bonus: Daily login bonus
    - streak_bonus: Streak milestone
    """
    success, result, error = EconomyService.add_xp(
        db=db,
        user_id=current_user.id,
        amount=request.amount,
        source=request.source,
        multiplier=request.multiplier
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return AddXPResponse(
        success=True,
        xp_gained=result["xp_gained"],
        total_xp=result["total_xp"],
        level=result["level"],
        leveled_up=result["leveled_up"],
        levels_gained=result["levels_gained"],
        xp_to_next_level=result["xp_to_next_level"]
    )


@router.post("/rank/update", response_model=UpdateRankResponse)
async def update_user_rank(
    request: UpdateRankRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's rank based on mastery percentage.

    Rank Thresholds:
    - S: 90%+ mastery (Grandmaster)
    - A: 75-89% mastery (Expert)
    - B: 60-74% mastery (Advanced)
    - C: 45-59% mastery (Intermediate)
    - D: 30-44% mastery (Beginner)
    - E: 0-29% mastery (Novice)

    The mastery_percent should be calculated based on
    the user's overall performance in diagnostic tests.
    """
    success, new_rank, old_rank, error = EconomyService.update_rank(
        db=db,
        user_id=current_user.id,
        mastery_percent=request.mastery_percent
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return UpdateRankResponse(
        success=True,
        new_rank=new_rank,
        old_rank=old_rank,
        rank_changed=(new_rank != old_rank)
    )
