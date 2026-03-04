import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Set, Optional

# --- path hack to import backend modules ---
# Assuming cwd is the project root or apps/websocket.
# We need to add the project root to sys.path to access 'apps.backend'.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) # Up two levels: apps/websocket -> apps -> root
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'apps', 'backend'))

import redis.asyncio as redis
from websockets.server import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

# Import JWT verification from backend
try:
    from jose import JWTError, jwt as jose_jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: python-jose not installed, JWT verification disabled")

# Import Backend Services
try:
    from app.core.database import SessionLocal
    from app.core.config import settings
    from app.services.dungeon_service import DungeonService
    # from app.services.boss_raid_service import BossRaidService # For later
except ImportError as e:
    print(f"Warning: Could not import backend services: {e}")
    # Fallback to prevent crash during simple testing if path is wrong
    SessionLocal = None
    DungeonService = None
    settings = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# JWT Configuration - use backend settings or environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "")
if settings:
    JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = "HS256"
if settings:
    JWT_ALGORITHM = settings.ALGORITHM


class AuthenticatedConnection:
    """Wrapper for authenticated WebSocket connections"""
    def __init__(self, websocket: WebSocketServerProtocol, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.user_id: Optional[str] = None
        self.authenticated: bool = False
        self.connected_at: datetime = datetime.now()


class GameWebSocketServer:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocketServerProtocol]] = {
            "global": set(),
            "battles": set(),
            "dungeons": set(),
        }
        # Track authenticated connections by websocket
        self.authenticated_connections: Dict[WebSocketServerProtocol, AuthenticatedConnection] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pubsub: Optional[redis.client.PubSub] = None

    async def connect_redis(self):
        """Connect to Redis for pub/sub functionality"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis")

            # Set up pub/sub
            self.redis_pubsub = self.redis_client.pubsub()
            await self.redis_pubsub.subscribe("game_events")

            # Start listening for Redis messages
            asyncio.create_task(self.listen_redis_messages())

        except Exception as e:
            logger.warning(f"Redis connection failed (optional): {str(e)}")
            self.redis_client = None

    async def listen_redis_messages(self):
        """Listen for Redis pub/sub messages and broadcast to WebSocket clients"""
        if not self.redis_pubsub:
            return

        try:
            async for message in self.redis_pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await self.broadcast_to_room(data.get("room", "global"), data)
        except Exception as e:
            logger.error(f"Redis listener error: {str(e)}")

    async def broadcast_to_room(self, room: str, message: dict):
        """Broadcast message to all connections in a room"""
        if room in self.connections:
            disconnected = set()
            for websocket in self.connections[room]:
                try:
                    await websocket.send(json.dumps(message))
                except ConnectionClosed:
                    disconnected.add(websocket)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {str(e)}")
                    disconnected.add(websocket)

            # Remove disconnected clients
            self.connections[room] -= disconnected

    async def _authenticate(self, websocket: WebSocketServerProtocol, data: dict) -> Optional[str]:
        """
        Authenticate user via JWT token.
        Returns user_id if valid, None if invalid.
        """
        token = data.get("token")
        if not token:
            await websocket.send(json.dumps({
                "type": "error",
                "code": "AUTH_REQUIRED",
                "message": "Authentication token required"
            }))
            return None

        # Check if JWT verification is available
        if not JWT_AVAILABLE:
            logger.warning("JWT verification not available - allowing connection without auth")
            # In development, extract user_id from data if provided
            return data.get("user_id")

        # Check if JWT_SECRET is configured
        if not JWT_SECRET:
            logger.error("JWT_SECRET not configured - rejecting authentication")
            await websocket.send(json.dumps({
                "type": "error",
                "code": "SERVER_CONFIG_ERROR",
                "message": "Server authentication not configured"
            }))
            return None

        try:
            # Verify JWT and extract user_id
            payload = jose_jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": True}
            )
            user_id = payload.get("sub")

            if not user_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "code": "INVALID_TOKEN",
                    "message": "Token missing user identifier"
                }))
                return None

            # Check token type (should be access token)
            token_type = payload.get("type", "access")
            if token_type != "access":
                await websocket.send(json.dumps({
                    "type": "error",
                    "code": "INVALID_TOKEN_TYPE",
                    "message": "Invalid token type for WebSocket authentication"
                }))
                return None

            return user_id

        except jose_jwt.ExpiredSignatureError:
            await websocket.send(json.dumps({
                "type": "error",
                "code": "TOKEN_EXPIRED",
                "message": "Token has expired"
            }))
            return None
        except jose_jwt.JWTClaimsError as e:
            await websocket.send(json.dumps({
                "type": "error",
                "code": "INVALID_CLAIMS",
                "message": f"Token claims error: {str(e)}"
            }))
            return None
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            await websocket.send(json.dumps({
                "type": "error",
                "code": "INVALID_TOKEN",
                "message": "Invalid authentication token"
            }))
            return None
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}")
            await websocket.send(json.dumps({
                "type": "error",
                "code": "AUTH_ERROR",
                "message": "Authentication failed"
            }))
            return None

    def _get_authenticated_user(self, websocket: WebSocketServerProtocol) -> Optional[str]:
        """Get authenticated user_id for a websocket connection"""
        conn = self.authenticated_connections.get(websocket)
        if conn and conn.authenticated:
            return conn.user_id
        return None

    async def _require_auth(self, websocket: WebSocketServerProtocol, action: str) -> Optional[str]:
        """
        Require authentication for an action.
        Returns user_id if authenticated, sends error and returns None otherwise.
        """
        user_id = self._get_authenticated_user(websocket)
        if not user_id:
            await websocket.send(json.dumps({
                "type": "error",
                "code": "UNAUTHORIZED",
                "message": f"Authentication required for {action}",
                "action": action
            }))
            return None
        return user_id

    def _validate_user_id_match(self, websocket: WebSocketServerProtocol, provided_user_id: str) -> bool:
        """
        Validate that provided user_id matches the authenticated user.
        Prevents users from performing actions as other users.
        """
        authenticated_user_id = self._get_authenticated_user(websocket)
        if not authenticated_user_id:
            return False
        return authenticated_user_id == provided_user_id

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle individual WebSocket connections"""
        client_id = f"client_{uuid.uuid4().hex[:12]}"

        # Create connection wrapper
        conn = AuthenticatedConnection(websocket, client_id)
        self.authenticated_connections[websocket] = conn

        try:
            # Add to global connections
            self.connections["global"].add(websocket)

            # Send welcome message - client must authenticate before game actions
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to ICFES Leveling Game Server",
                "client_id": client_id,
                "server_time": datetime.now().isoformat(),
                "version": "2.2.0-AUTH",
                "port": 4002,
                "auth_required": True,
                "instructions": "Send { type: 'authenticate', token: '<jwt>' } to authenticate"
            }))

            logger.info(f"Client connected: {client_id}")

            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data, client_id)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
                    await websocket.send(json.dumps({"type": "error", "message": str(e)}))

        except ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        finally:
            # Clean up authenticated connection
            if websocket in self.authenticated_connections:
                del self.authenticated_connections[websocket]
            for room in self.connections.values():
                room.discard(websocket)

    async def handle_message(self, websocket: WebSocketServerProtocol, data: dict, client_id: str):
        """
        Main Game Logic Router
        Delegates actions to DungeonService for real gameplay logic.
        Requires authentication for game actions.
        """
        message_type = data.get("type")
        logger.debug(f"Received message type '{message_type}' from {client_id}")

        # --- AUTHENTICATION ---
        if message_type == "authenticate":
            user_id = await self._authenticate(websocket, data)
            if user_id:
                conn = self.authenticated_connections.get(websocket)
                if conn:
                    conn.user_id = user_id
                    conn.authenticated = True
                    logger.info(f"Client {client_id} authenticated as user {user_id}")
                    await websocket.send(json.dumps({
                        "type": "authenticated",
                        "user_id": user_id,
                        "message": "Successfully authenticated",
                        "timestamp": datetime.now().isoformat()
                    }))
            return

        # --- UTILITIES (no auth required) ---
        if message_type == "ping":
            await websocket.send(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat(),
                "authenticated": self._get_authenticated_user(websocket) is not None
            }))
            return

        # --- GAME LOGIC (auth required) ---

        if message_type == "join_dungeon":
            # 1. Join Dungeon Logic - requires auth
            await self._handle_join_dungeon(websocket, data, client_id)

        elif message_type == "submit_answer":
            # 2. Combat Logic (Attack Step) - requires auth
            await self._handle_submit_answer(websocket, data, client_id)

        elif message_type == "subscribe":
            # Subscribe to room - requires auth for game rooms
            room = data.get("room", "global")

            # Allow global subscription without auth, but game rooms need auth
            if room != "global":
                user_id = await self._require_auth(websocket, f"subscribe to {room}")
                if not user_id:
                    return

            if room not in self.connections:
                self.connections[room] = set()
            self.connections[room].add(websocket)
            await websocket.send(json.dumps({
                "type": "subscribed",
                "room": room,
                "authenticated": self._get_authenticated_user(websocket) is not None
            }))

        else:
            # Unknown message type - check if authenticated first
            user_id = self._get_authenticated_user(websocket)
            if not user_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "code": "AUTH_REQUIRED",
                    "message": "Please authenticate first with { type: 'authenticate', token: '<jwt>' }"
                }))
            else:
                await websocket.send(json.dumps({
                    "type": "echo",
                    "original": data,
                    "user_id": user_id
                }))

    # --------------------------------------------------------------------------
    # GAME HANDLERS
    # --------------------------------------------------------------------------

    async def _handle_join_dungeon(self, websocket, data: dict, client_id: str):
        """
        Starts a dungeon run via DungeonService.
        Expects: { "type": "join_dungeon", "gate_id": "...", "user_id": "..." }
        Requires authentication and user_id must match authenticated user.
        """
        # Require authentication
        auth_user_id = await self._require_auth(websocket, "join_dungeon")
        if not auth_user_id:
            return

        if not DungeonService or not SessionLocal:
            await websocket.send(json.dumps({"type": "error", "message": "Backend services not available"}))
            return

        gate_id = data.get("gate_id")
        user_id = data.get("user_id")

        if not gate_id or not user_id:
            await websocket.send(json.dumps({"type": "error", "message": "Missing gate_id or user_id"}))
            return

        # Validate user_id matches authenticated user
        if not self._validate_user_id_match(websocket, user_id):
            await websocket.send(json.dumps({
                "type": "error",
                "code": "USER_MISMATCH",
                "message": "Cannot perform actions for other users"
            }))
            logger.warning(f"User mismatch: {auth_user_id} tried to act as {user_id}")
            return

        # Execute Service Call in ThreadPool (since DB is synchronous blocking)
        try:
            response = await asyncio.to_thread(self._sync_enter_gate, user_id, gate_id)

            if response.get("success"):
                # Join the specific dungeon room for updates
                run_id = response.get("run_id")
                dungeon_room = f"dungeon_{run_id}"
                if dungeon_room not in self.connections:
                    self.connections[dungeon_room] = set()
                self.connections[dungeon_room].add(websocket)

                await websocket.send(json.dumps({
                    "type": "dungeon_started",
                    "data": response
                }))
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": response.get("message", "Failed to join dungeon")
                }))

        except Exception as e:
            logger.error(f"Error in join_dungeon: {e}")
            await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    def _sync_enter_gate(self, user_id: str, gate_id: str) -> dict:
        """Synchronous wrapper for DungeonService.enter_gate"""
        db = SessionLocal()
        try:
            service = DungeonService(db)
            return service.enter_gate(user_id=user_id, gate_id=gate_id)
        finally:
            db.close()

    async def _handle_submit_answer(self, websocket, data: dict, client_id: str):
        """
        Processes answers for an encounter.
        Expects: { "encounter_id": "...", "user_id": "...", "answers": ["..."] }
        Requires authentication and user_id must match authenticated user.
        """
        # Require authentication
        auth_user_id = await self._require_auth(websocket, "submit_answer")
        if not auth_user_id:
            return

        if not DungeonService or not SessionLocal:
            await websocket.send(json.dumps({"type": "error", "message": "Backend services not available"}))
            return

        encounter_id = data.get("encounter_id")
        user_id = data.get("user_id")
        answers = data.get("answers", [])

        if not encounter_id or not user_id:
             await websocket.send(json.dumps({"type": "error", "message": "Missing match data"}))
             return

        # Validate user_id matches authenticated user
        if not self._validate_user_id_match(websocket, user_id):
            await websocket.send(json.dumps({
                "type": "error",
                "code": "USER_MISMATCH",
                "message": "Cannot perform actions for other users"
            }))
            logger.warning(f"User mismatch: {auth_user_id} tried to act as {user_id}")
            return

        try:
            result = await asyncio.to_thread(
                self._sync_submit_answer,
                encounter_id, user_id, answers
            )

            # Broadcast result to the user (and anyone watching this dungeon run)
            await websocket.send(json.dumps({
                "type": "battle_update",
                "data": result
            }))

        except Exception as e:
            logger.error(f"Error in submit_answer: {e}")
            await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    def _sync_submit_answer(self, encounter_id: str, user_id: str, answers: list) -> dict:
        """Synchronous wrapper for DungeonService.submit_encounter_answers"""
        db = SessionLocal()
        try:
            service = DungeonService(db)
            return service.submit_encounter_answers(encounter_id, user_id, answers)
        finally:
            db.close()


async def start_server():
    """Start the WebSocket server"""
    server = GameWebSocketServer()
    await server.connect_redis()

    port = int(os.getenv("PORT", 4002))
    host = "0.0.0.0"

    # Log JWT configuration status
    if JWT_AVAILABLE and JWT_SECRET:
        print(f"JWT Authentication: ENABLED")
    elif not JWT_AVAILABLE:
        print(f"WARNING: JWT Authentication: DISABLED (python-jose not installed)")
    else:
        print(f"WARNING: JWT Authentication: DISABLED (JWT_SECRET not configured)")

    print(f"CONQUEST MODE GAME SERVER running on ws://{host}:{port}")
    logger.info(f"Starting Game Server on {host}:{port}")

    async with serve(server.handle_connection, host, port):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(start_server())
