import asyncio
import json
import redis.asyncio as redis
import structlog
from websockets.server import serve, WebSocketServerProtocol
from typing import Dict, Set
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class GameWebSocketServer:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = None
        self.connections: Dict[str, Set[WebSocketServerProtocol]] = {
            "global": set(),
            "battles": set(),
            "leaderboard": set()
        }
        self.user_connections: Dict[str, WebSocketServerProtocol] = {}
    
    async def connect_redis(self):
        """Connect to Redis for pub/sub"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        client_id = f"client_{id(websocket)}"
        logger.info("New WebSocket connection", client_id=client_id, path=path)
        
        try:
            # Add to global connections
            self.connections["global"].add(websocket)
            
            async for message in websocket:
                await self.handle_message(websocket, message, client_id)
                
        except Exception as e:
            logger.error("WebSocket error", client_id=client_id, error=str(e))
        finally:
            await self.handle_disconnection(websocket, client_id)
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str, client_id: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            logger.info("Received message", client_id=client_id, type=message_type)
            
            if message_type == "auth":
                await self.handle_auth(websocket, data, client_id)
            elif message_type == "join_battle":
                await self.handle_join_battle(websocket, data, client_id)
            elif message_type == "leave_battle":
                await self.handle_leave_battle(websocket, data, client_id)
            elif message_type == "battle_action":
                await self.handle_battle_action(websocket, data, client_id)
            elif message_type == "ping":
                await websocket.send(json.dumps({"type": "pong", "timestamp": asyncio.get_event_loop().time()}))
            else:
                logger.warning("Unknown message type", client_id=client_id, type=message_type)
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message", client_id=client_id)
        except Exception as e:
            logger.error("Error handling message", client_id=client_id, error=str(e))
    
    async def handle_auth(self, websocket: WebSocketServerProtocol, data: dict, client_id: str):
        """Handle user authentication"""
        user_id = data.get("user_id")
        if user_id:
            self.user_connections[user_id] = websocket
            await websocket.send(json.dumps({
                "type": "auth_success",
                "user_id": user_id,
                "message": "Authentication successful"
            }))
            logger.info("User authenticated", user_id=user_id, client_id=client_id)
        else:
            await websocket.send(json.dumps({
                "type": "auth_error",
                "message": "Invalid user_id"
            }))
    
    async def handle_join_battle(self, websocket: WebSocketServerProtocol, data: dict, client_id: str):
        """Handle joining a battle room"""
        battle_id = data.get("battle_id")
        if battle_id:
            room_key = f"battle_{battle_id}"
            if room_key not in self.connections:
                self.connections[room_key] = set()
            self.connections[room_key].add(websocket)
            
            await websocket.send(json.dumps({
                "type": "joined_battle",
                "battle_id": battle_id,
                "message": f"Joined battle {battle_id}"
            }))
            logger.info("User joined battle", battle_id=battle_id, client_id=client_id)
    
    async def handle_leave_battle(self, websocket: WebSocketServerProtocol, data: dict, client_id: str):
        """Handle leaving a battle room"""
        battle_id = data.get("battle_id")
        if battle_id:
            room_key = f"battle_{battle_id}"
            if room_key in self.connections:
                self.connections[room_key].discard(websocket)
            
            await websocket.send(json.dumps({
                "type": "left_battle",
                "battle_id": battle_id,
                "message": f"Left battle {battle_id}"
            }))
            logger.info("User left battle", battle_id=battle_id, client_id=client_id)
    
    async def handle_battle_action(self, websocket: WebSocketServerProtocol, data: dict, client_id: str):
        """Handle battle actions (answer question, etc.)"""
        battle_id = data.get("battle_id")
        action = data.get("action")
        
        if battle_id and action:
            # Broadcast to battle room
            room_key = f"battle_{battle_id}"
            if room_key in self.connections:
                message = json.dumps({
                    "type": "battle_update",
                    "battle_id": battle_id,
                    "action": action,
                    "data": data.get("data", {}),
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # Send to all connections in the battle room
                await self.broadcast_to_room(room_key, message)
                logger.info("Battle action broadcasted", battle_id=battle_id, action=action)
    
    async def handle_disconnection(self, websocket: WebSocketServerProtocol, client_id: str):
        """Handle WebSocket disconnection"""
        logger.info("WebSocket disconnected", client_id=client_id)
        
        # Remove from all rooms
        for room_name, connections in self.connections.items():
            connections.discard(websocket)
        
        # Remove from user connections
        user_id = None
        for uid, conn in self.user_connections.items():
            if conn == websocket:
                user_id = uid
                break
        
        if user_id:
            del self.user_connections[user_id]
            logger.info("User disconnected", user_id=user_id)
    
    async def broadcast_to_room(self, room_name: str, message: str):
        """Broadcast message to all connections in a room"""
        if room_name in self.connections:
            disconnected = set()
            for websocket in self.connections[room_name]:
                try:
                    await websocket.send(message)
                except Exception as e:
                    logger.error("Failed to send message", error=str(e))
                    disconnected.add(websocket)
            
            # Remove disconnected websockets
            self.connections[room_name] -= disconnected
    
    async def broadcast_to_all(self, message: str):
        """Broadcast message to all global connections"""
        await self.broadcast_to_room("global", message)
    
    async def publish_to_redis(self, channel: str, message: dict):
        """Publish message to Redis channel"""
        if self.redis_client:
            try:
                await self.redis_client.publish(channel, json.dumps(message))
            except Exception as e:
                logger.error("Failed to publish to Redis", error=str(e))
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8001):
        """Start the WebSocket server"""
        await self.connect_redis()
        
        logger.info("Starting WebSocket server", host=host, port=port)
        
        async with serve(self.handle_connection, host, port):
            logger.info("WebSocket server started successfully")
            await asyncio.Future()  # run forever

async def main():
    """Main function"""
    server = GameWebSocketServer()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main()) 