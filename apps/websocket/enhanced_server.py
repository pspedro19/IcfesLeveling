"""
Enhanced WebSocket Server for ICFES Leveling
Real-time features for battles, guilds, diagnostics, and collaborative learning
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, List, Any
from dataclasses import dataclass, asdict
import jwt
from enum import Enum

import redis.asyncio as redis
from websockets.server import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Tipos de mensajes WebSocket"""
    # Sistema
    WELCOME = "welcome"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Autenticación
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    
    # Salas y usuarios
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_UPDATE = "room_update"
    USER_STATUS = "user_status"
    
    # Batallas
    BATTLE_START = "battle_start"
    BATTLE_ACTION = "battle_action"
    BATTLE_UPDATE = "battle_update"
    BATTLE_END = "battle_end"
    
    # Diagnóstico
    DIAGNOSTIC_START = "diagnostic_start"
    DIAGNOSTIC_QUESTION = "diagnostic_question"
    DIAGNOSTIC_ANSWER = "diagnostic_answer"
    DIAGNOSTIC_PROGRESS = "diagnostic_progress"
    DIAGNOSTIC_COMPLETE = "diagnostic_complete"
    
    # Guilds
    GUILD_CHAT = "guild_chat"
    GUILD_EVENT = "guild_event"
    GUILD_BATTLE = "guild_battle"
    GUILD_NOTIFICATION = "guild_notification"
    
    # Raids
    RAID_START = "raid_start"
    RAID_JOIN = "raid_join"
    RAID_ACTION = "raid_action"
    RAID_UPDATE = "raid_update"
    RAID_COMPLETE = "raid_complete"
    
    # Estudio colaborativo
    STUDY_SESSION_START = "study_session_start"
    STUDY_SESSION_JOIN = "study_session_join"
    STUDY_PROGRESS = "study_progress"
    STUDY_HELP_REQUEST = "study_help_request"
    
    # Notificaciones
    NOTIFICATION = "notification"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    LEVEL_UP = "level_up"
    RANK_UP = "rank_up"

@dataclass
class Client:
    """Representa un cliente conectado"""
    id: str
    websocket: WebSocketServerProtocol
    user_id: Optional[str] = None
    username: Optional[str] = None
    authenticated: bool = False
    rooms: Set[str] = None
    connected_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.rooms is None:
            self.rooms = {"global"}
        if self.connected_at is None:
            self.connected_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "authenticated": self.authenticated,
            "rooms": list(self.rooms),
            "connected_at": self.connected_at.isoformat()
        }

class EnhancedWebSocketServer:
    def __init__(self):
        self.clients: Dict[str, Client] = {}
        self.rooms: Dict[str, Set[str]] = {
            "global": set(),
            "battles": set(),
            "guilds": set(),
            "raids": set(),
            "diagnostic": set(),
            "study": set()
        }
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pubsub: Optional[redis.client.PubSub] = None
        self.jwt_secret = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
        
        # Estado de batallas activas
        self.active_battles: Dict[str, dict] = {}
        self.active_raids: Dict[str, dict] = {}
        self.study_sessions: Dict[str, dict] = {}
        
        # Configuración
        self.heartbeat_interval = 30  # segundos
        self.client_timeout = 90  # segundos
    
    async def connect_redis(self):
        """Conectar a Redis para pub/sub y caché"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Connected to Redis")
            
            # Configurar pub/sub
            self.redis_pubsub = self.redis_client.pubsub()
            await self.redis_pubsub.subscribe(
                "game_events",
                "battle_events",
                "guild_events",
                "diagnostic_events",
                "study_events"
            )
            
            # Iniciar listener de Redis
            asyncio.create_task(self.listen_redis_messages())
            
            # Iniciar heartbeat
            asyncio.create_task(self.heartbeat_loop())
            
        except Exception as e:
            logger.warning(f"Redis connection failed (running without cache): {str(e)}")
            self.redis_client = None
    
    async def listen_redis_messages(self):
        """Escuchar mensajes de Redis pub/sub"""
        if not self.redis_pubsub:
            return
        
        try:
            async for message in self.redis_pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        channel = message["channel"]
                        
                        # Enrutar mensaje según el canal
                        if channel == "battle_events":
                            await self.handle_battle_event(data)
                        elif channel == "guild_events":
                            await self.handle_guild_event(data)
                        elif channel == "diagnostic_events":
                            await self.handle_diagnostic_event(data)
                        elif channel == "study_events":
                            await self.handle_study_event(data)
                        else:
                            await self.broadcast_to_room(data.get("room", "global"), data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
        except Exception as e:
            logger.error(f"Redis listener error: {str(e)}")
    
    async def heartbeat_loop(self):
        """Enviar heartbeat a todos los clientes"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                current_time = datetime.now()
                disconnected = []
                
                for client_id, client in self.clients.items():
                    # Verificar timeout
                    if (current_time - client.last_activity).seconds > self.client_timeout:
                        disconnected.append(client_id)
                        continue
                    
                    # Enviar ping
                    try:
                        await client.websocket.send(json.dumps({
                            "type": MessageType.PING.value,
                            "timestamp": current_time.isoformat()
                        }))
                    except:
                        disconnected.append(client_id)
                
                # Desconectar clientes inactivos
                for client_id in disconnected:
                    await self.disconnect_client(client_id)
                    
            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
    
    async def authenticate_client(self, client: Client, token: str) -> bool:
        """Autenticar cliente con JWT"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            client.user_id = payload.get("sub")
            client.username = payload.get("username", "Anonymous")
            client.authenticated = True
            
            # Guardar en Redis
            if self.redis_client:
                await self.redis_client.hset(
                    f"ws:user:{client.user_id}",
                    mapping={
                        "client_id": client.id,
                        "username": client.username,
                        "connected_at": client.connected_at.isoformat()
                    }
                )
                await self.redis_client.expire(f"ws:user:{client.user_id}", 3600)
            
            return True
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return False
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Manejar nueva conexión WebSocket"""
        client_id = f"client_{uuid.uuid4().hex[:12]}"
        client = Client(id=client_id, websocket=websocket)
        
        try:
            # Registrar cliente
            self.clients[client_id] = client
            self.rooms["global"].add(client_id)
            
            # Enviar mensaje de bienvenida
            await websocket.send(json.dumps({
                "type": MessageType.WELCOME.value,
                "client_id": client_id,
                "server_time": datetime.now().isoformat(),
                "version": "3.0.0",
                "features": [
                    "real_time_battles",
                    "guild_chat",
                    "diagnostic_tests",
                    "collaborative_study",
                    "raid_battles"
                ]
            }))
            
            logger.info(f"Client connected: {client_id} from path: {path}")
            
            # Procesar mensajes del cliente
            async for message in websocket:
                try:
                    data = json.loads(message)
                    client.last_activity = datetime.now()
                    await self.handle_client_message(client, data)
                except json.JSONDecodeError:
                    await self.send_error(client, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
                    await self.send_error(client, str(e))
                    
        except ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
        finally:
            await self.disconnect_client(client_id)
    
    async def handle_client_message(self, client: Client, data: dict):
        """Procesar mensaje del cliente"""
        msg_type = data.get("type")
        
        if msg_type == MessageType.PONG.value:
            # Actualizar última actividad
            client.last_activity = datetime.now()
            
        elif msg_type == MessageType.AUTH.value:
            # Autenticar cliente
            token = data.get("token")
            if await self.authenticate_client(client, token):
                await client.websocket.send(json.dumps({
                    "type": MessageType.AUTH_SUCCESS.value,
                    "user_id": client.user_id,
                    "username": client.username
                }))
            else:
                await client.websocket.send(json.dumps({
                    "type": MessageType.AUTH_FAILED.value,
                    "error": "Invalid token"
                }))
        
        elif msg_type == MessageType.JOIN_ROOM.value:
            # Unirse a sala
            room = data.get("room")
            if room and room in self.rooms:
                client.rooms.add(room)
                self.rooms[room].add(client.id)
                await self.broadcast_room_update(room)
                
        elif msg_type == MessageType.LEAVE_ROOM.value:
            # Salir de sala
            room = data.get("room")
            if room and room in client.rooms:
                client.rooms.remove(room)
                self.rooms[room].discard(client.id)
                await self.broadcast_room_update(room)
        
        elif msg_type == MessageType.BATTLE_ACTION.value:
            # Acción de batalla
            await self.handle_battle_action(client, data)
            
        elif msg_type == MessageType.DIAGNOSTIC_ANSWER.value:
            # Respuesta de diagnóstico
            await self.handle_diagnostic_answer(client, data)
            
        elif msg_type == MessageType.GUILD_CHAT.value:
            # Chat del guild
            await self.handle_guild_chat(client, data)
            
        elif msg_type == MessageType.RAID_ACTION.value:
            # Acción de raid
            await self.handle_raid_action(client, data)
            
        elif msg_type == MessageType.STUDY_HELP_REQUEST.value:
            # Solicitud de ayuda en estudio
            await self.handle_study_help(client, data)
        
        else:
            await self.send_error(client, f"Unknown message type: {msg_type}")
    
    async def handle_battle_action(self, client: Client, data: dict):
        """Manejar acción de batalla"""
        battle_id = data.get("battle_id")
        action = data.get("action")
        
        if battle_id not in self.active_battles:
            await self.send_error(client, "Battle not found")
            return
        
        battle = self.active_battles[battle_id]
        
        # Procesar acción (simplificado)
        battle["actions"].append({
            "user_id": client.user_id,
            "action": action,
            "timestamp": datetime.now().isoformat()
        })
        
        # Broadcast actualización de batalla
        await self.broadcast_to_room("battles", {
            "type": MessageType.BATTLE_UPDATE.value,
            "battle_id": battle_id,
            "battle": battle
        })
        
        # Guardar en Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"battle:{battle_id}",
                "data",
                json.dumps(battle)
            )
    
    async def handle_diagnostic_answer(self, client: Client, data: dict):
        """Manejar respuesta de diagnóstico"""
        test_id = data.get("test_id")
        question_id = data.get("question_id")
        answer = data.get("answer")
        time_spent = data.get("time_spent")
        
        # Broadcast progreso del diagnóstico
        await self.broadcast_to_room("diagnostic", {
            "type": MessageType.DIAGNOSTIC_PROGRESS.value,
            "test_id": test_id,
            "user_id": client.user_id,
            "question_id": question_id,
            "progress": data.get("progress", 0)
        })
        
        # Guardar en Redis
        if self.redis_client:
            await self.redis_client.lpush(
                f"diagnostic:{test_id}:answers",
                json.dumps({
                    "user_id": client.user_id,
                    "question_id": question_id,
                    "answer": answer,
                    "time_spent": time_spent,
                    "timestamp": datetime.now().isoformat()
                })
            )
    
    async def handle_guild_chat(self, client: Client, data: dict):
        """Manejar chat del guild"""
        if not client.authenticated:
            await self.send_error(client, "Authentication required")
            return
        
        guild_id = data.get("guild_id")
        message = data.get("message")
        
        # Broadcast mensaje a miembros del guild
        await self.broadcast_to_room(f"guild:{guild_id}", {
            "type": MessageType.GUILD_CHAT.value,
            "guild_id": guild_id,
            "user_id": client.user_id,
            "username": client.username,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_raid_action(self, client: Client, data: dict):
        """Manejar acción de raid"""
        raid_id = data.get("raid_id")
        action = data.get("action")
        
        if raid_id not in self.active_raids:
            # Crear nuevo raid si no existe
            self.active_raids[raid_id] = {
                "id": raid_id,
                "participants": [],
                "boss_hp": 10000,
                "start_time": datetime.now().isoformat(),
                "actions": []
            }
        
        raid = self.active_raids[raid_id]
        
        # Agregar participante si es nuevo
        if client.user_id not in [p["user_id"] for p in raid["participants"]]:
            raid["participants"].append({
                "user_id": client.user_id,
                "username": client.username,
                "damage_dealt": 0
            })
        
        # Procesar acción
        damage = action.get("damage", 0)
        raid["boss_hp"] -= damage
        raid["actions"].append({
            "user_id": client.user_id,
            "action": action,
            "damage": damage,
            "timestamp": datetime.now().isoformat()
        })
        
        # Actualizar daño del participante
        for p in raid["participants"]:
            if p["user_id"] == client.user_id:
                p["damage_dealt"] += damage
        
        # Verificar si el raid terminó
        if raid["boss_hp"] <= 0:
            raid["completed"] = True
            raid["end_time"] = datetime.now().isoformat()
            
            await self.broadcast_to_room("raids", {
                "type": MessageType.RAID_COMPLETE.value,
                "raid_id": raid_id,
                "raid": raid
            })
            
            # Limpiar raid después de completarlo
            del self.active_raids[raid_id]
        else:
            # Broadcast actualización del raid
            await self.broadcast_to_room("raids", {
                "type": MessageType.RAID_UPDATE.value,
                "raid_id": raid_id,
                "raid": raid
            })
    
    async def handle_study_help(self, client: Client, data: dict):
        """Manejar solicitud de ayuda en estudio"""
        topic = data.get("topic")
        question = data.get("question")
        
        # Broadcast solicitud de ayuda a tutores y estudiantes avanzados
        await self.broadcast_to_room("study", {
            "type": MessageType.STUDY_HELP_REQUEST.value,
            "user_id": client.user_id,
            "username": client.username,
            "topic": topic,
            "question": question,
            "timestamp": datetime.now().isoformat()
        })
        
        # Guardar en Redis para matchmaking
        if self.redis_client:
            await self.redis_client.lpush(
                "study:help_requests",
                json.dumps({
                    "user_id": client.user_id,
                    "topic": topic,
                    "question": question,
                    "timestamp": datetime.now().isoformat()
                })
            )
    
    async def handle_battle_event(self, data: dict):
        """Manejar evento de batalla desde Redis"""
        battle_id = data.get("battle_id")
        event_type = data.get("event_type")
        
        if event_type == "start":
            self.active_battles[battle_id] = data.get("battle", {})
            await self.broadcast_to_room("battles", {
                "type": MessageType.BATTLE_START.value,
                "battle_id": battle_id,
                "battle": self.active_battles[battle_id]
            })
        elif event_type == "end":
            if battle_id in self.active_battles:
                await self.broadcast_to_room("battles", {
                    "type": MessageType.BATTLE_END.value,
                    "battle_id": battle_id,
                    "winner": data.get("winner"),
                    "rewards": data.get("rewards", {})
                })
                del self.active_battles[battle_id]
    
    async def handle_guild_event(self, data: dict):
        """Manejar evento de guild desde Redis"""
        guild_id = data.get("guild_id")
        event_type = data.get("event_type")
        
        await self.broadcast_to_room(f"guild:{guild_id}", {
            "type": MessageType.GUILD_EVENT.value,
            "guild_id": guild_id,
            "event_type": event_type,
            "data": data
        })
    
    async def handle_diagnostic_event(self, data: dict):
        """Manejar evento de diagnóstico desde Redis"""
        test_id = data.get("test_id")
        event_type = data.get("event_type")
        
        if event_type == "complete":
            await self.broadcast_to_room("diagnostic", {
                "type": MessageType.DIAGNOSTIC_COMPLETE.value,
                "test_id": test_id,
                "user_id": data.get("user_id"),
                "results": data.get("results", {})
            })
    
    async def handle_study_event(self, data: dict):
        """Manejar evento de estudio desde Redis"""
        session_id = data.get("session_id")
        event_type = data.get("event_type")
        
        if event_type == "session_start":
            self.study_sessions[session_id] = data.get("session", {})
            await self.broadcast_to_room("study", {
                "type": MessageType.STUDY_SESSION_START.value,
                "session_id": session_id,
                "session": self.study_sessions[session_id]
            })
    
    async def broadcast_to_room(self, room: str, message: dict):
        """Broadcast mensaje a todos los clientes en una sala"""
        if room not in self.rooms:
            return
        
        disconnected = []
        for client_id in self.rooms[room]:
            if client_id in self.clients:
                client = self.clients[client_id]
                try:
                    await client.websocket.send(json.dumps(message))
                except ConnectionClosed:
                    disconnected.append(client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {str(e)}")
                    disconnected.append(client_id)
        
        # Limpiar clientes desconectados
        for client_id in disconnected:
            await self.disconnect_client(client_id)
    
    async def broadcast_room_update(self, room: str):
        """Broadcast actualización de sala"""
        users_in_room = []
        for client_id in self.rooms.get(room, set()):
            if client_id in self.clients:
                client = self.clients[client_id]
                if client.authenticated:
                    users_in_room.append({
                        "user_id": client.user_id,
                        "username": client.username
                    })
        
        await self.broadcast_to_room(room, {
            "type": MessageType.ROOM_UPDATE.value,
            "room": room,
            "users": users_in_room,
            "user_count": len(users_in_room)
        })
    
    async def send_error(self, client: Client, error: str):
        """Enviar mensaje de error al cliente"""
        try:
            await client.websocket.send(json.dumps({
                "type": MessageType.ERROR.value,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }))
        except:
            pass
    
    async def disconnect_client(self, client_id: str):
        """Desconectar cliente y limpiar recursos"""
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        
        # Eliminar de todas las salas
        for room in list(client.rooms):
            self.rooms[room].discard(client_id)
            await self.broadcast_room_update(room)
        
        # Limpiar Redis
        if self.redis_client and client.user_id:
            await self.redis_client.delete(f"ws:user:{client.user_id}")
        
        # Eliminar cliente
        del self.clients[client_id]
        logger.info(f"Client disconnected and cleaned up: {client_id}")

async def main():
    """Iniciar servidor WebSocket"""
    server = EnhancedWebSocketServer()
    
    # Conectar a Redis
    await server.connect_redis()
    
    # Configurar puerto
    port = int(os.getenv("WEBSOCKET_PORT", 4002))
    host = "0.0.0.0"
    
    logger.info(f"Starting Enhanced WebSocket server on {host}:{port}")
    
    # Iniciar servidor
    async with serve(server.handle_connection, host, port):
        logger.info(f"WebSocket server running on ws://{host}:{port}")
        await asyncio.Future()  # Ejecutar indefinidamente

if __name__ == "__main__":
    asyncio.run(main())