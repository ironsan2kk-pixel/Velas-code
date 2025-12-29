/**
 * VELAS - Pairs Page
 * Страница со списком всех 20 торговых пар
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardContent, Badge, Spinner, Input, Select } from '@/components/ui';
import { usePairs } from '@/hooks/useApi';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity,
  Search,
  ArrowUpDown,
  Filter,
} from 'lucide-react';
import type { Pair, VolatilityRegime } from '@/types';

type SortField = 'symbol' | 'price_change_percent_24h' | 'volume_24h' | 'win_rate' | 'pnl_percent';
type SortDirection = 'asc' | 'desc';

const Pairs: React.FC = () => {
  const navigate = useNavigate();
  const { data: pairsResp, isLoading } = usePairs();
  const pairs = pairsResp?.data || [];
  
  const [searchQuery, setSearchQuery] = useState('');
  const [sectorFilter, setSectorFilter] = useState<string>('all');
  const [volatilityFilter, setVolatilityFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('symbol');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // Фильтрация
  const filteredPairs = pairs?.filter((pair) => {
    const matchesSearch = pair.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         pair.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector = sectorFilter === 'all' || pair.sector === sectorFilter;
    const matchesVolatility = volatilityFilter === 'all' || pair.volatility_regime === volatilityFilter;
    
    return matchesSearch && matchesSector && matchesVolatility;
  }) || [];

  // Сортировка
  const sortedPairs = [...filteredPairs].sort((a, b) => {
    let aValue: any = a[sortField];
    let bValue: any = b[sortField];
    
    if (sortField === 'symbol' || sortField === 'name') {
      aValue = aValue?.toLowerCase() || '';
      bValue = bValue?.toLowerCase() || '';
    }
    
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  // Toggle сортировка
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Уникальные сектора
  const sectors = ['all', ...new Set(pairs?.map((p) => p.sector) || [])];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-dark-text-primary">Торговые пары</h1>
        <p className="text-dark-text-secondary mt-1">
          Мониторинг 20 криптовалютных пар
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="py-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input
              placeholder="Поиск по паре..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={<Search className="w-4 h-4" />}
            />
            
            <Select
              value={sectorFilter}
              onChange={(e) => setSectorFilter(e.target.value)}
              options={sectors.map((s) => ({ value: s, label: s === 'all' ? 'Все секторы' : s }))}
            />
            
            <Select
              value={volatilityFilter}
              onChange={(e) => setVolatilityFilter(e.target.value)}
              options={[
                { value: 'all', label: 'Вся волатильность' },
                { value: 'LOW', label: 'Низкая' },
                { value: 'NORMAL', label: 'Нормальная' },
                { value: 'HIGH', label: 'Высокая' },
              ]}
            />
            
            <div className="flex items-center gap-2 text-sm text-dark-text-muted">
              <Filter className="w-4 h-4" />
              <span>Найдено: {sortedPairs.length}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pairs Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-bg-secondary border-b border-dark-border">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <button
                      onClick={() => handleSort('symbol')}
                      className="flex items-center gap-1 text-sm font-medium text-dark-text-primary hover:text-accent-blue"
                    >
                      Пара
                      <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-medium text-dark-text-primary">
                    Сектор
                  </th>
                  <th className="px-6 py-3 text-right text-sm font-medium text-dark-text-primary">
                    Цена
                  </th>
                  <th className="px-6 py-3 text-right">
                    <button
                      onClick={() => handleSort('price_change_percent_24h')}
                      className="flex items-center gap-1 text-sm font-medium text-dark-text-primary hover:text-accent-blue ml-auto"
                    >
                      24h %
                      <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="px-6 py-3 text-right">
                    <button
                      onClick={() => handleSort('volume_24h')}
                      className="flex items-center gap-1 text-sm font-medium text-dark-text-primary hover:text-accent-blue ml-auto"
                    >
                      Объём 24h
                      <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-medium text-dark-text-primary">
                    Волатильность
                  </th>
                  <th className="px-6 py-3 text-right">
                    <button
                      onClick={() => handleSort('win_rate')}
                      className="flex items-center gap-1 text-sm font-medium text-dark-text-primary hover:text-accent-blue ml-auto"
                    >
                      WinRate
                      <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="px-6 py-3 text-right">
                    <button
                      onClick={() => handleSort('pnl_percent')}
                      className="flex items-center gap-1 text-sm font-medium text-dark-text-primary hover:text-accent-blue ml-auto"
                    >
                      P&L %
                      <ArrowUpDown className="w-3 h-3" />
                    </button>
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-medium text-dark-text-primary">
                    Позиция
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-border">
                {sortedPairs.map((pair) => (
                  <tr
                    key={pair.symbol}
                    onClick={() => navigate(`/pairs/${pair.symbol}`)}
                    className="hover:bg-dark-bg-hover cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-dark-text-primary">{pair.symbol}</div>
                        <div className="text-sm text-dark-text-muted">{pair.name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant="secondary" size="sm">
                        {pair.sector}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-dark-text-primary">
                      ${pair.current_price.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className={`flex items-center justify-end gap-1 ${
                        pair.price_change_percent_24h >= 0 ? 'text-profit' : 'text-loss'
                      }`}>
                        {pair.price_change_percent_24h >= 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        <span className="font-medium">
                          {pair.price_change_percent_24h >= 0 ? '+' : ''}
                          {pair.price_change_percent_24h.toFixed(2)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-dark-text-secondary">
                      ${(pair.volume_24h / 1_000_000).toFixed(1)}M
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Badge
                        variant={
                          pair.volatility_regime === 'LOW' ? 'info' :
                          pair.volatility_regime === 'HIGH' ? 'danger' : 'warning'
                        }
                        size="sm"
                      >
                        {pair.volatility_regime}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className={`font-medium ${
                        pair.win_rate >= 70 ? 'text-profit' :
                        pair.win_rate >= 50 ? 'text-dark-text-primary' : 'text-loss'
                      }`}>
                        {pair.win_rate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className={`font-medium ${
                        pair.pnl_percent >= 0 ? 'text-profit' : 'text-loss'
                      }`}>
                        {pair.pnl_percent >= 0 ? '+' : ''}
                        {pair.pnl_percent.toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      {pair.active_position ? (
                        <Badge
                          variant={pair.active_position === 'LONG' ? 'success' : 'danger'}
                          size="sm"
                        >
                          {pair.active_position}
                        </Badge>
                      ) : (
                        <span className="text-dark-text-muted text-sm">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {sortedPairs.length === 0 && (
            <div className="text-center py-12 text-dark-text-muted">
              <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Пары не найдены</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Pairs;

