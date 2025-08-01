import uuid
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.base_class import Base

class NodeType(SAEnum):
    MONSTER = "monster"
    ELITE_MONSTER = "elite_monster"
    BOSS = "boss"
    TREASURE = "treasure"
    PVP_BATTLE = "pvp_battle"

class DungeonNode(Base):
    __tablename__ = "dungeon_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    node_type = Column(SAEnum(NodeType), nullable=False)
    name = Column(String, nullable=False)
    difficulty = Column(Integer, default=1)

class PlayerDungeonState(Base):
    __tablename__ = "player_dungeon_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    node_id = Column(UUID(as_uuid=True), ForeignKey("dungeon_nodes.id"), nullable=False)
    
    player = relationship("User")
    node = relationship("DungeonNode")

    __table_args__ = (
        UniqueConstraint('player_id', 'node_id', name='_player_node_uc'),
    )
