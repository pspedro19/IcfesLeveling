'use client';

import React from 'react';
import { Sword, Shield, FlaskConical as Potion, Gem, Star, Sparkles } from 'lucide-react';
import InventorySystem from '../components/Inventory/InventorySystem';
import { useInventoryStore } from '../stores/useInventoryStore';

// Icon mapping for items
const ITEM_ICONS: Record<string, React.ReactNode> = {
  'sword-1': <Sword className="w-8 h-8" />,
  'shield-1': <Shield className="w-8 h-8" />,
  'potion-1': <Potion className="w-8 h-8" />,
  'potion-2': <Potion className="w-8 h-8" />,
  'gem-1': <Gem className="w-8 h-8" />,
  'gem-2': <Sparkles className="w-8 h-8" />,
  'special-1': <Star className="w-8 h-8" />
};

export default function InventoryPage() {
  const { items, equipItem, useItem, removeItem, addItem } = useInventoryStore();
  
  // Add icons to items
  const itemsWithIcons = items.map(item => ({
    ...item,
    icon: ITEM_ICONS[item.id] || null
  }));
  
  const handleEquip = (itemId: string) => {
    const item = items.find(i => i.id === itemId);
    if (item?.equipped) {
      // Unequip
      equipItem(itemId);
    } else {
      equipItem(itemId);
    }
  };
  
  const handleUse = (itemId: string) => {
    useItem(itemId);
    console.log(`Used item: ${itemId}`);
  };
  
  const handleDrop = (itemId: string) => {
    removeItem(itemId);
    console.log(`Dropped item: ${itemId}`);
  };
  
  // Demo: Add random item
  const addRandomItem = () => {
    const randomItems = [
      {
        id: `shield-${Date.now()}`,
        name: 'Escudo de la Sabiduría',
        type: 'armor' as const,
        rarity: 'epic' as const,
        quantity: 1,
        stats: { hp: 20, wisdom: 10 },
        description: 'Un escudo que protege tanto el cuerpo como la mente.',
        value: 750
      },
      {
        id: `potion-${Date.now()}`,
        name: 'Elixir de Experiencia',
        type: 'consumable' as const,
        rarity: 'rare' as const,
        quantity: 3,
        description: 'Duplica la experiencia ganada durante 5 minutos.',
        value: 150
      },
      {
        id: `gem-${Date.now()}`,
        name: 'Rubí del Poder',
        type: 'material' as const,
        rarity: 'legendary' as const,
        quantity: 1,
        description: 'Una gema extremadamente rara con poder infinito.',
        value: 1000
      }
    ];
    
    const randomItem = randomItems[Math.floor(Math.random() * randomItems.length)];
    addItem(randomItem);
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white text-center mb-8 font-cinzel">
          Sistema de Inventario
        </h1>
        
        {/* Demo Controls */}
        <div className="bg-gray-900/80 rounded-lg p-4 mb-6 text-center">
          <button
            onClick={addRandomItem}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 
              hover:to-purple-800 text-white font-bold px-6 py-3 rounded-lg transition-all
              transform hover:scale-105"
          >
            Añadir Item Aleatorio
          </button>
          <p className="text-gray-400 text-sm mt-2">
            Haz clic para añadir items de prueba al inventario
          </p>
        </div>
        
        {/* Inventory Component */}
        <InventorySystem
          items={itemsWithIcons}
          onEquip={handleEquip}
          onUse={handleUse}
          onDrop={handleDrop}
        />
        
        {/* Instructions */}
        <div className="mt-8 bg-gray-900/80 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">
            Instrucciones
          </h3>
          <ul className="space-y-2 text-gray-300">
            <li>• Haz clic en un item para ver sus detalles</li>
            <li>• Arrastra y suelta items para reorganizar</li>
            <li>• Equipa armas y armaduras desde el menú de detalles</li>
            <li>• Usa consumibles para activar sus efectos</li>
            <li>• Filtra items por tipo usando las pestañas superiores</li>
          </ul>
        </div>
      </div>
    </div>
  );
}