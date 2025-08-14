import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface InventoryItem {
  id: string;
  name: string;
  type: 'weapon' | 'armor' | 'consumable' | 'material' | 'special';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
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

interface InventoryState {
  items: InventoryItem[];
  capacity: number;
  gold: number;
  
  // Actions
  addItem: (item: InventoryItem) => void;
  removeItem: (itemId: string) => void;
  equipItem: (itemId: string) => void;
  unequipItem: (itemId: string) => void;
  useItem: (itemId: string) => void;
  updateQuantity: (itemId: string, quantity: number) => void;
  sellItem: (itemId: string) => number;
  clearInventory: () => void;
}

export const useInventoryStore = create<InventoryState>()(
  persist(
    (set) => ({
      items: [
        // Initial demo items
        {
          id: 'sword-1',
          name: 'Espada del Conocimiento',
          type: 'weapon',
          rarity: 'rare',
          quantity: 1,
          equipped: true,
          stats: { power: 15, wisdom: 5 },
          description: 'Una espada forjada con sabiduría antigua.',
          value: 500
        },
        {
          id: 'potion-1',
          name: 'Poción de Concentración',
          type: 'consumable',
          rarity: 'common',
          quantity: 5,
          description: 'Aumenta tu enfoque durante las batallas.',
          value: 50
        },
        {
          id: 'gem-1',
          name: 'Cristal de Experiencia',
          type: 'material',
          rarity: 'epic',
          quantity: 3,
          description: 'Cristal puro que contiene experiencia condensada.',
          value: 200
        }
      ],
      capacity: 40,
      gold: 1000,
      
      addItem: (item) => set((state) => {
        const existingItem = state.items.find(i => i.id === item.id);
        
        if (existingItem && item.type !== 'weapon' && item.type !== 'armor') {
          // Stack consumables and materials
          return {
            items: state.items.map(i => 
              i.id === item.id 
                ? { ...i, quantity: i.quantity + item.quantity }
                : i
            )
          };
        }
        
        // Add new item if capacity allows
        if (state.items.length < state.capacity) {
          return { items: [...state.items, item] };
        }
        
        return state; // Inventory full
      }),
      
      removeItem: (itemId) => set((state) => ({
        items: state.items.filter(item => item.id !== itemId)
      })),
      
      equipItem: (itemId) => set((state) => ({
        items: state.items.map(item => {
          if (item.id === itemId) {
            return { ...item, equipped: true };
          }
          // Unequip other items of same type
          if (item.equipped && 
              state.items.find(i => i.id === itemId)?.type === item.type) {
            return { ...item, equipped: false };
          }
          return item;
        })
      })),
      
      unequipItem: (itemId) => set((state) => ({
        items: state.items.map(item => 
          item.id === itemId ? { ...item, equipped: false } : item
        )
      })),
      
      useItem: (itemId) => set((state) => ({
        items: state.items.map(item => {
          if (item.id === itemId && item.type === 'consumable') {
            const newQuantity = item.quantity - 1;
            return newQuantity > 0 
              ? { ...item, quantity: newQuantity }
              : null;
          }
          return item;
        }).filter(Boolean) as InventoryItem[]
      })),
      
      updateQuantity: (itemId, quantity) => set((state) => ({
        items: quantity > 0 
          ? state.items.map(item => 
              item.id === itemId ? { ...item, quantity } : item
            )
          : state.items.filter(item => item.id !== itemId)
      })),
      
      sellItem: (itemId) => set((state) => {
        const item = state.items.find(i => i.id === itemId);
        if (!item) return state;
        
        return {
          items: state.items.filter(i => i.id !== itemId),
          gold: state.gold + item.value
        };
      }),
      
      clearInventory: () => set({ items: [], gold: 0 })
    }),
    {
      name: 'inventory-storage'
    }
  )
);