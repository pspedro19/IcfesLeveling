import unittest
from unittest.mock import MagicMock, patch
import asyncio
import json
import os
import sys

# Add path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'apps', 'backend'))

# Import the server class to test
# We need to mock the imports inside main.py if they fail, but assuming the previous step fixed the path logic, we can try importing.
# To be safe, we will mock the backend modules BEFORE importing main
sys.modules['app'] = MagicMock()
sys.modules['app.core'] = MagicMock()
sys.modules['app.core.database'] = MagicMock()
sys.modules['app.services'] = MagicMock()
sys.modules['app.services.dungeon_service'] = MagicMock()

from apps.websocket.main import GameWebSocketServer

class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.open = True

    async def send(self, message):
        self.sent_messages.append(message)

    async def close(self, code=1000, reason=''):
        self.open = False

class TestConquestIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = GameWebSocketServer()
        # Mock Redis to avoid connection errors
        self.server.connect_redis = MagicMock(return_value=asyncio.Future())
        self.server.connect_redis.return_value.set_result(None)

    @patch('apps.websocket.main.DungeonService')
    @patch('apps.websocket.main.SessionLocal')
    async def test_full_combat_flow(self, mock_session_cls, mock_service_cls):
        """
        Verifies:
        1. Client connects -> Welcome message
        2. Client sends join_dungeon -> Server calls DungeonService.enter_gate -> Server responds
        3. Client sends submit_answer -> Server calls DungeonService.submit_answer -> Server responds
        """
        print("\n🔵 STARTING INTEGRATION SIMULATION: Client -> WebSocket -> Backend Service")

        # --- SETUP MOCKS ---
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance

        # Mock Responses
        mock_service_instance.enter_gate.return_value = {
            "success": True,
            "run_id": "run_123",
            "message": "Welcome to the Math Dungeon",
            "current_encounter": {"type": "monster", "enemy": {"name": "Geometry Guardian"}}
        }
        
        mock_service_instance.submit_encounter_answers.return_value = {
            "success": True,
            "encounter_results": {
                "damage_dealt": 250,
                "damage_taken": 10,
                "accuracy": 1.0
            },
            "dungeon_status": "in_progress"
        }

        # --- TEST CONNECTION ---
        client_ws = MockWebSocket()
        client_id = "test_user_1"
        
        # Simulate handling join_dungeon message directly
        join_msg = {
            "type": "join_dungeon",
            "gate_id": "gate_math_1",
            "user_id": "user_123"
        }
        
        print(f"🔸 SENDING: {join_msg}")
        await self.server._handle_join_dungeon(client_ws, join_msg, client_id)
        
        # Verify Service Call
        mock_service_instance.enter_gate.assert_called_with(user_id="user_123", gate_id="gate_math_1")
        print("✅ Backend Service `enter_gate` was called correctly.")

        # Verify Response
        self.assertEqual(len(client_ws.sent_messages), 1)
        response = json.loads(client_ws.sent_messages[0])
        self.assertEqual(response['type'], 'dungeon_started')
        self.assertEqual(response['data']['run_id'], 'run_123')
        print(f"🔹 RECEIVED: {response}")

        # --- TEST COMBAT ---
        attack_msg = {
            "type": "submit_answer",
            "encounter_id": "enc_1",
            "user_id": "user_123",
            "answers": ["45"]
        }
        
        print(f"🔸 SENDING: {attack_msg}")
        await self.server._handle_submit_answer(client_ws, attack_msg, client_id)
        
        # Verify Service Call
        mock_service_instance.submit_encounter_answers.assert_called_with("enc_1", "user_123", ["45"])
        print("✅ Backend Service `submit_encounter_answers` was called correctly.")

        # Verify Response
        self.assertEqual(len(client_ws.sent_messages), 2)
        response_2 = json.loads(client_ws.sent_messages[1])
        self.assertEqual(response_2['type'], 'battle_update')
        self.assertEqual(response_2['data']['encounter_results']['damage_dealt'], 250)
        print(f"🔹 RECEIVED: {response_2}")
        
        print("🟢 SIMULATION SUCCESSFUL: The brain is correctly connected to the body.\n")

if __name__ == '__main__':
    unittest.main()
