import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Set, Optional

import redis.asyncio as redis
from websockets.server import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GameWebSocketServer:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocketServerProtocol]] = {
            "global": set(),
            "battles": set(),
            "guilds": set(),
            "raids": set(),
            "diagnostic": set()  # Added for diagnostic tests
        }
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pubsub: Optional[redis.client.PubSub] = None

    async def connect_redis(self):
        """Connect to Redis for pub/sub functionality"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")  # Changed to localhost
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
            # Don't raise - allow WebSocket to work without Redis
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

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle individual WebSocket connections"""
        client_id = f"client_{uuid.uuid4().hex[:12]}"
        
        try:
            # Add to global connections
            self.connections["global"].add(websocket)
            
            # Send welcome message with more info
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to ICFES Leveling WebSocket",
                "client_id": client_id,
                "server_time": datetime.now().isoformat(),
                "version": "2.0.0",
                "port": 4002  # Confirm port in welcome message
            }))
            
            logger.info(f"Client connected: {client_id}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data, client_id)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message from client: {client_id}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Internal server error"
                    }))
                    
        except ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Connection error for client {client_id}: {str(e)}")
        finally:
            # Remove from all rooms
            for room in self.connections.values():
                room.discard(websocket)
            logger.info(f"Cleaned up connection for {client_id}")

    async def handle_message(self, websocket: WebSocketServerProtocol, data: dict, client_id: str):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        
        logger.debug(f"Received message type '{message_type}' from {client_id}")
        
        if message_type == "ping":
            await websocket.send(json.dumps({
                "type": "pong", 
                "timestamp": data.get("timestamp"),
                "server_time": datetime.now().isoformat()
            }))
            
        elif message_type == "subscribe":
            room = data.get("room", "global")
            if room not in self.connections:
                self.connections[room] = set()
            self.connections[room].add(websocket)
            await websocket.send(json.dumps({
                "type": "subscribed",
                "room": room,
                "message": f"Successfully subscribed to {room}"
            }))
            logger.info(f"Client {client_id} subscribed to room {room}")
            
        elif message_type == "unsubscribe":
            room = data.get("room", "global")
            if room in self.connections:
                self.connections[room].discard(websocket)
            await websocket.send(json.dumps({
                "type": "unsubscribed",
                "room": room,
                "message": f"Successfully unsubscribed from {room}"
            }))
            logger.info(f"Client {client_id} unsubscribed from room {room}")
            
        elif message_type == "broadcast":
            room = data.get("room", "global")
            message = data.get("message", {})
            message["sender_id"] = client_id
            message["timestamp"] = datetime.now().isoformat()
            await self.broadcast_to_room(room, message)
            
        elif message_type == "diagnostic_update":
            # Handle diagnostic test updates
            await self.broadcast_to_room("diagnostic", {
                "type": "diagnostic_update",
                "data": data.get("data", {}),
                "sender_id": client_id,
                "timestamp": datetime.now().isoformat()
            })
            
        elif message_type == "leaderboard_update":
            # Handle leaderboard updates
            await self.broadcast_to_room("global", {
                "type": "leaderboard_update",
                "data": data.get("data", {}),
                "timestamp": datetime.now().isoformat()
            })
            
        else:
            # Echo back unknown message types
            await websocket.send(json.dumps({
                "type": "echo",
                "original": data,
                "message": f"Unknown message type: {message_type}"
            }))

async def start_server():
    """Start the WebSocket server"""
    server = GameWebSocketServer()
    
    # Try to connect to Redis (optional)
    await server.connect_redis()
    
    # ✅ FIXED: Changed default port from 8000 to 4002
    port = int(os.getenv("PORT", 4002))  # Changed from 8000 to 4002
    host = "0.0.0.0"
    
    print("=" * 60)
    print(f"🔌 ICFES LEVELING WEBSOCKET SERVER")
    print("=" * 60)
    print(f"📍 Starting on: ws://{host}:{port}")
    print(f"🔧 Port: {port}")
    print(f"🌍 Host: {host}")
    print(f"⏰ Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    try:
        # Create a custom handler with CORS support
        async def cors_handler(websocket, path):
            try:
                # Add CORS headers for WebSocket (simplified)
                if hasattr(websocket, 'request_headers'):
                    origin = websocket.request_headers.get("origin")
                    if origin:
                        logger.debug(f"WebSocket connection from origin: {origin}")
                
                await server.handle_connection(websocket, path)
            except Exception as e:
                logger.error(f"Connection handler error: {e}")
                if websocket.open:
                    await websocket.close(1011, "Internal server error")
        
        async with serve(
            cors_handler, 
            host, 
            port,
            ping_interval=30,  # Send ping every 30 seconds
            ping_timeout=10,    # Wait 10 seconds for pong
        ):
            print(f"✅ WebSocket server started successfully on ws://{host}:{port}")
            print("Press Ctrl+C to stop the server")
            print("=" * 60)
            logger.info(f"WebSocket server started successfully on {host}:{port}")
            await asyncio.Future()  # run forever
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {str(e)}")
        print(f"❌ Failed to start server: {str(e)}")
        raise

# Health check endpoint for Docker
async def health_check():
    """Simple health check for Docker"""
    return {"status": "healthy", "service": "websocket", "timestamp": datetime.utcnow().isoformat()}

# Add simple HTTP health check server (optional)
async def run_health_server():
    """Run a simple HTTP server for health checks on port 5002"""
    from aiohttp import web
    
    async def health_handler(request):
        return web.json_response({
            "status": "healthy",
            "service": "websocket",
            "port": 4002,
            "timestamp": datetime.now().isoformat()
        })
    
    app = web.Application()
    app.router.add_get('/health', health_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5002)
    await site.start()
    logger.info("Health check server running on http://0.0.0.0:5002/health")

async def main():
    """Main entry point with optional health check server"""
    # Start health check server in background (optional)
    try:
        asyncio.create_task(run_health_server())
    except Exception as e:
        logger.warning(f"Health check server not started (optional): {e}")
    
    # Start main WebSocket server
    await start_server()

if __name__ == "__main__":
    # Check if aiohttp is available for health check
    try:
        import aiohttp
        asyncio.run(main())
    except ImportError:
        print("⚠️  aiohttp not installed, running without health check server")
        print("   Install with: pip install aiohttp")
        asyncio.run(start_server())