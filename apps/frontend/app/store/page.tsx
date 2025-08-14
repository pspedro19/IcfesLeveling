'use client';
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ShoppingCart, Coins, Gem, Zap, Star, Crown, Shield, Clock, Target, TrendingUp, Package, History, Wallet } from 'lucide-react';

interface StoreItem {
  id: string;
  name: string;
  description: string;
  item_type: string;
  rarity: string;
  icon_url: string;
  store_price_orbs: number;
  store_price_crystals: number;
  is_cosmetic: boolean;
  is_power_up: boolean;
  power_up_effect: any;
}

interface UserCurrency {
  orbs: number;
  crystals: number;
  total_earned_orbs: number;
  total_earned_crystals: number;
}

interface StoreInventory {
  cosmetic_items: StoreItem[];
  power_up_items: StoreItem[];
  user_currency: UserCurrency;
}

interface StoreTransaction {
  id: string;
  item_id: string;
  transaction_type: string;
  currency_type: string;
  amount_spent: number;
  quantity: number;
  transaction_date: string;
  status: string;
  item: StoreItem;
}

const rarityColors = {
  common: '#6c757d',
  rare: '#007bff',
  epic: '#6f42c1',
  legendary: '#fd7e14'
};

const rarityIcons = {
  common: <Star className="w-4 h-4" />,
  rare: <Star className="w-4 h-4 fill-current" />,
  epic: <Crown className="w-4 h-4" />,
  legendary: <Crown className="w-4 h-4 fill-current" />
};

const powerUpIcons = {
  double_xp: <TrendingUp className="w-5 h-5" />,
  time_extension: <Clock className="w-5 h-5" />,
  hint_master: <Target className="w-5 h-5" />,
  perfect_score_boost: <Star className="w-5 h-5" />,
  shield: <Shield className="w-5 h-5" />,
  critical_boost: <Zap className="w-5 h-5" />
};

export default function StorePage() {
  const [inventory, setInventory] = useState<StoreInventory | null>(null);
  const [transactions, setTransactions] = useState<StoreTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<'cosmetics' | 'power-ups'>('cosmetics');
  const [purchaseLoading, setPurchaseLoading] = useState<string | null>(null);
  const [showTransactions, setShowTransactions] = useState(false);

  useEffect(() => {
    fetchStoreData();
  }, []);

  const fetchStoreData = async () => {
    try {
      const [inventoryRes, transactionsRes] = await Promise.all([
        fetch('/api/v1/store/inventory'),
        fetch('/api/v1/store/transactions?limit=10')
      ]);

      if (inventoryRes.ok) {
        const inventoryData = await inventoryRes.json();
        setInventory(inventoryData);
      }

      if (transactionsRes.ok) {
        const transactionsData = await transactionsRes.json();
        setTransactions(transactionsData);
      }
    } catch (error) {
      console.error('Error fetching store data:', error);
    } finally {
      setLoading(false);
    }
  };

  const purchaseItem = async (item: StoreItem, currencyType: 'orbs' | 'crystals') => {
    setPurchaseLoading(item.id);
    try {
      const response = await fetch('/api/v1/store/purchase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_id: item.id,
          quantity: 1,
          currency_type: currencyType
        })
      });

      if (response.ok) {
        const result = await response.json();
        // Refresh store data
        await fetchStoreData();
        alert(`¡Compra exitosa! ${result.message}`);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error purchasing item:', error);
      alert('Error al realizar la compra');
    } finally {
      setPurchaseLoading(null);
    }
  };

  const getRarityColor = (rarity: string) => {
    return rarityColors[rarity as keyof typeof rarityColors] || '#6c757d';
  };

  const getRarityIcon = (rarity: string) => {
    return rarityIcons[rarity as keyof typeof rarityIcons] || <Star className="w-4 h-4" />;
  };

  const getPowerUpIcon = (effect: any) => {
    const effectType = effect?.effect;
    return powerUpIcons[effectType as keyof typeof powerUpIcons] || <Zap className="w-5 h-5" />;
  };

  const formatCurrency = (amount: number) => {
    return amount.toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Cargando tienda...</div>
      </div>
    );
  }

  if (!inventory) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Error al cargar la tienda</div>
      </div>
    );
  }

  const currentItems = selectedCategory === 'cosmetics' ? inventory.cosmetic_items : inventory.power_up_items;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4 flex items-center justify-center gap-3">
            <ShoppingCart className="w-10 h-10 text-yellow-400" />
            Tienda Virtual
          </h1>
          <p className="text-blue-200 text-lg">
            Gasta tus monedas en items cosméticos y power-ups para mejorar tu experiencia
          </p>
        </motion.div>

        {/* Currency Display */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-8">
          <div className="flex flex-wrap justify-center gap-8">
            <div className="flex items-center gap-3 text-white">
              <Coins className="w-6 h-6 text-yellow-400" />
              <div>
                <div className="text-2xl font-bold">{formatCurrency(inventory.user_currency.orbs)}</div>
                <div className="text-sm text-blue-200">Orbes</div>
              </div>
            </div>
            <div className="flex items-center gap-3 text-white">
              <Gem className="w-6 h-6 text-purple-400" />
              <div>
                <div className="text-2xl font-bold">{formatCurrency(inventory.user_currency.crystals)}</div>
                <div className="text-sm text-blue-200">Cristales</div>
              </div>
            </div>
            <button
              onClick={() => setShowTransactions(!showTransactions)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <History className="w-4 h-4" />
              Historial
            </button>
          </div>
        </motion.div>

        {/* Transaction History */}
        {showTransactions && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-8">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <History className="w-5 h-5" />
              Historial de Transacciones
            </h3>
            <div className="space-y-3">
              {transactions.map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between bg-white/5 rounded-lg p-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                      <Package className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <div className="text-white font-medium">{transaction.item.name}</div>
                      <div className="text-blue-200 text-sm">
                        {transaction.currency_type === 'orbs' ? 'Orbes' : 'Cristales'}: {transaction.amount_spent}
                      </div>
                    </div>
                  </div>
                  <div className="text-blue-200 text-sm">
                    {new Date(transaction.transaction_date).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Category Tabs */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex justify-center mb-8">
          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-1">
            <button
              onClick={() => setSelectedCategory('cosmetics')}
              className={`px-6 py-3 rounded-lg transition-all ${
                selectedCategory === 'cosmetics'
                  ? 'bg-blue-600 text-white'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Items Cosméticos
            </button>
            <button
              onClick={() => setSelectedCategory('power-ups')}
              className={`px-6 py-3 rounded-lg transition-all ${
                selectedCategory === 'power-ups'
                  ? 'bg-blue-600 text-white'
                  : 'text-blue-200 hover:text-white'
              }`}
            >
              Power-ups
            </button>
          </div>
        </motion.div>

        {/* Items Grid */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {currentItems.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white/10 backdrop-blur-sm rounded-lg border border-white/20 overflow-hidden hover:border-white/40 transition-all"
              >
                {/* Item Image */}
                <div className="h-48 bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
                  {item.is_power_up ? (
                    getPowerUpIcon(item.power_up_effect)
                  ) : (
                    <div className="w-16 h-16 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                      <Crown className="w-8 h-8 text-white" />
                    </div>
                  )}
                </div>

                {/* Item Info */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-white font-semibold text-lg">{item.name}</h3>
                    <div className="flex items-center gap-1" style={{ color: getRarityColor(item.rarity) }}>
                      {getRarityIcon(item.rarity)}
                    </div>
                  </div>
                  
                  <p className="text-blue-200 text-sm mb-4">{item.description}</p>
                  
                  {/* Rarity Badge */}
                  <div className="mb-4">
                    <span
                      className="px-2 py-1 rounded-full text-xs font-medium"
                      style={{
                        backgroundColor: getRarityColor(item.rarity) + '20',
                        color: getRarityColor(item.rarity)
                      }}
                    >
                      {item.rarity.toUpperCase()}
                    </span>
                  </div>

                  {/* Purchase Buttons */}
                  <div className="space-y-2">
                    {item.store_price_orbs > 0 && (
                      <button
                        onClick={() => purchaseItem(item, 'orbs')}
                        disabled={purchaseLoading === item.id || inventory.user_currency.orbs < item.store_price_orbs}
                        className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all ${
                          inventory.user_currency.orbs >= item.store_price_orbs
                            ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                            : 'bg-gray-600 text-gray-300 cursor-not-allowed'
                        }`}
                      >
                        {purchaseLoading === item.id ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <>
                            <Coins className="w-4 h-4" />
                            {formatCurrency(item.store_price_orbs)} Orbes
                          </>
                        )}
                      </button>
                    )}
                    
                    {item.store_price_crystals > 0 && (
                      <button
                        onClick={() => purchaseItem(item, 'crystals')}
                        disabled={purchaseLoading === item.id || inventory.user_currency.crystals < item.store_price_crystals}
                        className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all ${
                          inventory.user_currency.crystals >= item.store_price_crystals
                            ? 'bg-purple-600 hover:bg-purple-700 text-white'
                            : 'bg-gray-600 text-gray-300 cursor-not-allowed'
                        }`}
                      >
                        {purchaseLoading === item.id ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <>
                            <Gem className="w-4 h-4" />
                            {formatCurrency(item.store_price_crystals)} Cristales
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Empty State */}
        {currentItems.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-12">
            <div className="text-blue-200 text-lg">
              No hay items disponibles en esta categoría
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
} 