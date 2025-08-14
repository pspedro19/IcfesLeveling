'use client';

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import { 
  Package, 
  Sword, 
  Shield, 
  Gem,
  FlaskConical as Potion,
  ScrollText,
  Star,
  X,
  Info,
  Sparkles,
  Crown,
  Zap
} from 'lucide-react';
import { useAudio } from '../PortalLogin/AudioEngine';
import { trackGameEvent } from '@/lib/analytics';

interface InventoryItem {
  id: string;
  name: string;
  type: 'weapon' | 'armor' | 'consumable' | 'material' | 'special';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  icon: React.ReactNode;
  quantity: number;
  equipped?: boolean;
  stats?: {
    power?: number;
    wisdom?: number;
    speed?: number;
    hp?: number;
    mp?: number;
  };
  description: string;
  value: number;
}

interface InventorySystemProps {
  items: InventoryItem[];
  onEquip?: (itemId: string) => void;
  onUse?: (itemId: string) => void;
  onDrop?: (itemId: string) => void;
  gridSize?: number;
}

const RARITY_COLORS = {
  common: 'from-gray-500 to-gray-600',
  rare: 'from-blue-500 to-blue-600',
  epic: 'from-purple-500 to-purple-600',
  legendary: 'from-yellow-500 to-yellow-600'
};

const RARITY_GLOW = {
  common: '',
  rare: 'shadow-blue-500/50',
  epic: 'shadow-purple-500/50',
  legendary: 'shadow-yellow-500/50'
};

const TYPE_ICONS = {
  weapon: <Sword className="w-6 h-6" />,
  armor: <Shield className="w-6 h-6" />,
  consumable: <Potion className="w-6 h-6" />,
  material: <Gem className="w-6 h-6" />,
  special: <Star className="w-6 h-6" />
};

export default function InventorySystem({ 
  items, 
  onEquip, 
  onUse, 
  onDrop,
  gridSize = 40
}: InventorySystemProps) {
  const { playSound } = useAudio();
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [draggedItem, setDraggedItem] = useState<InventoryItem | null>(null);
  const [draggedOver, setDraggedOver] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const inventoryRef = useRef<HTMLDivElement>(null);
  
  // Grid configuration
  const cols = 8;
  const rows = 5;
  const totalSlots = cols * rows;
  
  // Filter items by type
  const filteredItems = items.filter(item => {
    if (filter === 'all') return true;
    if (filter === 'equipped') return item.equipped;
    return item.type === filter;
  });
  
  // Create inventory grid with items
  const inventoryGrid = Array(totalSlots).fill(null).map((_, index) => {
    return filteredItems[index] || null;
  });
  
  const handleItemClick = (item: InventoryItem) => {
    playSound('typing_click');
    setSelectedItem(item);
    trackGameEvent('inventory_item_clicked', { 
      itemId: item.id,
      itemType: item.type,
      rarity: item.rarity
    });
  };
  
  const handleDragStart = (item: InventoryItem) => {
    setDraggedItem(item);
    playSound('quest_complete');
  };
  
  const handleDragEnd = (event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    if (!draggedItem || !inventoryRef.current) return;
    
    // Get grid position from drag end point
    const rect = inventoryRef.current.getBoundingClientRect();
    const x = info.point.x - rect.left;
    const y = info.point.y - rect.top;
    
    const col = Math.floor(x / (rect.width / cols));
    const row = Math.floor(y / (rect.height / rows));
    const targetIndex = row * cols + col;
    
    if (targetIndex >= 0 && targetIndex < totalSlots && targetIndex !== draggedOver) {
      // Move item to new position
      playSound('damage_hit');
      console.log(`Moving ${draggedItem.name} to slot ${targetIndex}`);
    }
    
    setDraggedItem(null);
    setDraggedOver(null);
  };
  
  const handleEquip = () => {
    if (!selectedItem || !onEquip) return;
    
    playSound('level_up');
    onEquip(selectedItem.id);
    trackGameEvent('inventory_item_equipped', { 
      itemId: selectedItem.id,
      itemName: selectedItem.name
    });
    setSelectedItem(null);
  };
  
  const handleUse = () => {
    if (!selectedItem || !onUse) return;
    
    playSound('quest_complete');
    onUse(selectedItem.id);
    trackGameEvent('inventory_item_used', { 
      itemId: selectedItem.id,
      itemName: selectedItem.name
    });
    
    // Close if consumable and quantity is 0
    if (selectedItem.type === 'consumable' && selectedItem.quantity <= 1) {
      setSelectedItem(null);
    }
  };
  
  const handleDrop = () => {
    if (!selectedItem || !onDrop) return;
    
    playSound('notification_epic');
    onDrop(selectedItem.id);
    trackGameEvent('inventory_item_dropped', { 
      itemId: selectedItem.id,
      itemName: selectedItem.name
    });
    setSelectedItem(null);
  };
  
  return (
    <div className="bg-gray-900/95 backdrop-blur-sm rounded-lg p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white font-cinzel flex items-center gap-2">
          <Package className="w-8 h-8 text-purple-400" />
          Inventario
        </h2>
        
        {/* Filter Tabs */}
        <div className="flex gap-2">
          {['all', 'weapon', 'armor', 'consumable', 'equipped'].map(type => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                filter === type
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {type === 'all' ? 'Todo' : 
               type === 'equipped' ? 'Equipado' :
               type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>
      
      {/* Inventory Grid */}
      <div
        ref={inventoryRef}
        className="grid grid-cols-8 gap-2 mb-6 bg-gray-800/50 rounded-lg p-4"
        style={{ minHeight: `${rows * 80}px` }}
      >
        {inventoryGrid.map((item, index) => (
          <motion.div
            key={`slot-${index}`}
            className={`
              aspect-square bg-gray-700/50 rounded-lg border-2 border-gray-600/50
              hover:border-gray-500 transition-all cursor-pointer relative
              ${draggedOver === index ? 'border-purple-500 bg-purple-900/30' : ''}
            `}
            onMouseEnter={() => draggedItem && setDraggedOver(index)}
            onMouseLeave={() => setDraggedOver(null)}
            whileHover={{ scale: item ? 1.05 : 1 }}
            whileTap={{ scale: 0.95 }}
          >
            {item && (
              <motion.div
                className="w-full h-full p-2 relative"
                onClick={() => handleItemClick(item)}
                drag
                dragElastic={0.2}
                dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
                onDragStart={() => handleDragStart(item)}
                onDragEnd={handleDragEnd}
                whileDrag={{ scale: 1.1, zIndex: 50 }}
              >
                {/* Rarity Background */}
                <div className={`
                  absolute inset-0 bg-gradient-to-br ${RARITY_COLORS[item.rarity]}
                  opacity-20 rounded-lg
                `} />
                
                {/* Item Icon */}
                <div className={`
                  w-full h-full flex items-center justify-center text-white
                  ${item.equipped ? 'ring-2 ring-yellow-400' : ''}
                `}>
                  {item.icon || TYPE_ICONS[item.type]}
                </div>
                
                {/* Quantity Badge */}
                {item.quantity > 1 && (
                  <div className="absolute bottom-0 right-0 bg-gray-900 text-white
                    text-xs font-bold px-1.5 py-0.5 rounded-tl-lg rounded-br-lg">
                    {item.quantity}
                  </div>
                )}
                
                {/* Equipped Badge */}
                {item.equipped && (
                  <div className="absolute top-0 right-0 text-yellow-400">
                    <Crown className="w-4 h-4" />
                  </div>
                )}
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
      
      {/* Item Stats */}
      <div className="bg-gray-800/50 rounded-lg p-4">
        <div className="text-center text-gray-400">
          <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Capacidad: {filteredItems.length} / {totalSlots}</p>
          <p className="text-sm mt-1">
            Arrastra items para reorganizar
          </p>
        </div>
      </div>
      
      {/* Item Detail Modal */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div
            className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedItem(null)}
          >
            <motion.div
              className="bg-gray-900 rounded-lg max-w-md w-full"
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              onClick={e => e.stopPropagation()}
            >
              {/* Item Header */}
              <div className={`
                bg-gradient-to-r ${RARITY_COLORS[selectedItem.rarity]} 
                p-6 rounded-t-lg relative overflow-hidden
              `}>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="absolute top-4 right-4 text-white/70 hover:text-white"
                >
                  <X className="w-6 h-6" />
                </button>
                
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 bg-black/30 rounded-lg flex items-center 
                    justify-center text-white">
                    {selectedItem.icon || TYPE_ICONS[selectedItem.type]}
                  </div>
                  
                  <div>
                    <h3 className="text-2xl font-bold text-white">
                      {selectedItem.name}
                    </h3>
                    <p className="text-white/80 capitalize">
                      {selectedItem.rarity} {selectedItem.type}
                    </p>
                    {selectedItem.equipped && (
                      <span className="text-yellow-300 text-sm flex items-center gap-1 mt-1">
                        <Crown className="w-4 h-4" />
                        Equipado
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Item Details */}
              <div className="p-6">
                <p className="text-gray-300 mb-4">
                  {selectedItem.description}
                </p>
                
                {/* Stats */}
                {selectedItem.stats && (
                  <div className="bg-gray-800 rounded-lg p-4 mb-4">
                    <h4 className="text-sm font-semibold text-gray-400 mb-3">
                      Estadísticas
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(selectedItem.stats).map(([stat, value]) => (
                        <div key={stat} className="flex items-center justify-between">
                          <span className="text-gray-400 capitalize">{stat}</span>
                          <span className="text-white font-semibold">
                            +{value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Value */}
                <div className="flex items-center justify-between mb-6">
                  <span className="text-gray-400">Valor</span>
                  <span className="text-yellow-400 font-semibold flex items-center gap-1">
                    <Gem className="w-4 h-4" />
                    {selectedItem.value} Orbes
                  </span>
                </div>
                
                {/* Actions */}
                <div className="flex gap-3">
                  {selectedItem.type === 'weapon' || selectedItem.type === 'armor' ? (
                    <button
                      onClick={handleEquip}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700
                        hover:from-purple-700 hover:to-purple-800 text-white font-bold
                        py-3 px-6 rounded-lg transition-all flex items-center 
                        justify-center gap-2"
                    >
                      <Zap className="w-5 h-5" />
                      {selectedItem.equipped ? 'Desequipar' : 'Equipar'}
                    </button>
                  ) : selectedItem.type === 'consumable' ? (
                    <button
                      onClick={handleUse}
                      className="flex-1 bg-gradient-to-r from-green-600 to-green-700
                        hover:from-green-700 hover:to-green-800 text-white font-bold
                        py-3 px-6 rounded-lg transition-all flex items-center 
                        justify-center gap-2"
                    >
                      <Sparkles className="w-5 h-5" />
                      Usar ({selectedItem.quantity})
                    </button>
                  ) : null}
                  
                  <button
                    onClick={handleDrop}
                    className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white
                      font-semibold rounded-lg transition-all"
                  >
                    Tirar
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}