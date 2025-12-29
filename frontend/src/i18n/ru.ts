// Russian translations for VELAS Dashboard

export const translations = {
  // Common
  common: {
    loading: 'Загрузка...',
    error: 'Ошибка',
    success: 'Успешно',
    cancel: 'Отмена',
    save: 'Сохранить',
    delete: 'Удалить',
    edit: 'Редактировать',
    close: 'Закрыть',
    open: 'Открыть',
    refresh: 'Обновить',
    search: 'Поиск',
    filter: 'Фильтр',
    export: 'Экспорт',
    import: 'Импорт',
    download: 'Скачать',
    all: 'Все',
    none: 'Нет',
    yes: 'Да',
    no: 'Нет',
    status: 'Статус',
    date: 'Дата',
    time: 'Время',
    actions: 'Действия',
    details: 'Детали',
    viewAll: 'Смотреть все',
    noData: 'Нет данных',
  },
  
  // Navigation
  nav: {
    dashboard: 'Главная',
    positions: 'Позиции',
    history: 'История',
    signals: 'Сигналы',
    pairs: 'Пары',
    analytics: 'Аналитика',
    backtest: 'Бэктест',
    settings: 'Настройки',
    alerts: 'Алерты',
    system: 'Система',
  },
  
  // Dashboard
  dashboard: {
    title: 'VELAS Trading System',
    systemStatus: 'Статус системы',
    totalPnL: 'Общий P&L',
    winRate: 'Win Rate',
    totalTrades: 'Сделок',
    portfolioHeat: 'Нагрузка портфеля',
    equityCurve: 'Кривая эквити',
    openPositions: 'Открытые позиции',
    recentSignals: 'Последние сигналы',
    manageAll: 'Управление',
    periods: {
      '1d': '1 День',
      '1w': '1 Неделя',
      '1m': '1 Месяц',
      '3m': '3 Месяца',
    },
  },
  
  // Positions
  positions: {
    title: 'Позиции',
    openPositions: 'Открытые позиции',
    closedPositions: 'Закрытые позиции',
    noOpenPositions: 'Нет открытых позиций',
    symbol: 'Пара',
    side: 'Направление',
    entry: 'Вход',
    current: 'Текущая',
    pnl: 'P&L',
    duration: 'Длительность',
    stopLoss: 'Stop Loss',
    takeProfit: 'Take Profit',
    closePosition: 'Закрыть позицию',
    confirmClose: 'Вы уверены, что хотите закрыть позицию?',
  },
  
  // History
  history: {
    title: 'История сделок',
    tradeHistory: 'История торговли',
    exitPrice: 'Выход',
    exitReason: 'Причина',
    exportCsv: 'Экспорт CSV',
    stats: {
      totalTrades: 'Всего сделок',
      winningTrades: 'Прибыльных',
      losingTrades: 'Убыточных',
      winRate: 'Win Rate',
      totalPnL: 'Общий P&L',
      avgPnL: 'Средний P&L',
      maxWin: 'Макс. выигрыш',
      maxLoss: 'Макс. убыток',
      profitFactor: 'Profit Factor',
      avgDuration: 'Ср. длительность',
    },
    exitReasons: {
      tp1: 'TP1',
      tp2: 'TP2',
      tp3: 'TP3',
      tp4: 'TP4',
      tp5: 'TP5',
      tp6: 'TP6',
      sl: 'Stop Loss',
      manual: 'Ручное закрытие',
      expired: 'Истёк срок',
    },
  },
  
  // Signals
  signals: {
    title: 'Сигналы',
    signalLog: 'Лог сигналов',
    pendingSignals: 'Ожидающие',
    activeSignals: 'Активные',
    newSignal: 'Новый сигнал',
    entryPrice: 'Цена входа',
    preset: 'Пресет',
    volatility: 'Волатильность',
    sentToTelegram: 'Отправлен в Telegram',
    statuses: {
      pending: 'Ожидает',
      active: 'Активен',
      filled: 'Исполнен',
      cancelled: 'Отменён',
      expired: 'Истёк',
    },
  },
  
  // Pairs
  pairs: {
    title: 'Торговые пары',
    allPairs: 'Все пары',
    price: 'Цена',
    change24h: 'Изменение 24ч',
    volume24h: 'Объём 24ч',
    high24h: 'Макс 24ч',
    low24h: 'Мин 24ч',
    volatility: 'Волатильность',
    activePosition: 'Активная позиция',
    lastSignal: 'Последний сигнал',
    sectors: {
      BTC: 'Bitcoin',
      ETH: 'Ethereum',
      L1: 'Layer 1',
      L2: 'Layer 2',
      DEFI: 'DeFi',
      OLD: 'Старые монеты',
      MEME: 'Мем-коины',
      CEX: 'CEX токены',
    },
  },
  
  // Analytics
  analytics: {
    title: 'Аналитика',
    performance: 'Производительность',
    equity: 'Эквити',
    drawdown: 'Просадка',
    monthlyReturns: 'Месячная доходность',
    pairPerformance: 'По парам',
    correlation: 'Корреляция',
    metrics: {
      sharpeRatio: 'Sharpe Ratio',
      profitFactor: 'Profit Factor',
      maxDrawdown: 'Макс. просадка',
      avgTradeDuration: 'Ср. длительность',
      bestPair: 'Лучшая пара',
      worstPair: 'Худшая пара',
    },
  },
  
  // Backtest
  backtest: {
    title: 'Бэктестинг',
    runBacktest: 'Запустить тест',
    results: 'Результаты',
    configuration: 'Конфигурация',
    symbol: 'Пара',
    timeframe: 'Таймфрейм',
    startDate: 'Начало',
    endDate: 'Конец',
    initialBalance: 'Начальный баланс',
    riskPerTrade: 'Риск на сделку',
    running: 'Выполняется...',
    completed: 'Завершён',
    failed: 'Ошибка',
  },
  
  // Settings
  settings: {
    title: 'Настройки',
    trading: 'Торговля',
    telegram: 'Telegram',
    system: 'Система',
    ui: 'Интерфейс',
    mode: 'Режим',
    paperMode: 'Paper Trading',
    liveMode: 'Live Trading',
    riskPerTrade: 'Риск на сделку',
    maxPositions: 'Макс. позиций',
    maxPerSector: 'Макс. на сектор',
    correlationLimit: 'Лимит корреляции',
    botToken: 'Bot Token',
    chatId: 'Chat ID',
    notifications: {
      newSignal: 'Новый сигнал',
      tpHit: 'Срабатывание TP',
      slHit: 'Срабатывание SL',
      systemErrors: 'Ошибки системы',
    },
    logLevel: 'Уровень логов',
    timezone: 'Часовой пояс',
    theme: 'Тема',
    darkTheme: 'Тёмная',
    lightTheme: 'Светлая',
    language: 'Язык',
    saved: 'Настройки сохранены',
  },
  
  // System
  system: {
    title: 'Система',
    status: 'Статус',
    logs: 'Логи',
    components: 'Компоненты',
    uptime: 'Время работы',
    version: 'Версия',
    build: 'Сборка',
    pauseTrading: 'Приостановить',
    resumeTrading: 'Возобновить',
    restart: 'Перезапустить',
    downloadLogs: 'Скачать логи',
    componentNames: {
      data_engine: 'Data Engine',
      strategy_engine: 'Strategy Engine',
      live_engine: 'Live Engine',
      telegram_bot: 'Telegram Bot',
      api_server: 'API Server',
    },
    statuses: {
      online: 'Онлайн',
      offline: 'Оффлайн',
      degraded: 'Деградация',
      maintenance: 'Обслуживание',
    },
    logLevels: {
      debug: 'DEBUG',
      info: 'INFO',
      warning: 'WARNING',
      error: 'ERROR',
    },
  },
  
  // Trading
  trading: {
    long: 'LONG',
    short: 'SHORT',
    buy: 'Купить',
    sell: 'Продать',
    entry: 'Вход',
    exit: 'Выход',
    stopLoss: 'Stop Loss',
    takeProfit: 'Take Profit',
    breakeven: 'Безубыток',
    cascade: 'Каскад',
  },
  
  // Time
  time: {
    now: 'Сейчас',
    today: 'Сегодня',
    yesterday: 'Вчера',
    thisWeek: 'На этой неделе',
    thisMonth: 'В этом месяце',
    ago: 'назад',
  },
  
  // Errors
  errors: {
    networkError: 'Ошибка сети',
    serverError: 'Ошибка сервера',
    notFound: 'Не найдено',
    unauthorized: 'Не авторизован',
    forbidden: 'Доступ запрещён',
    validationError: 'Ошибка валидации',
    unknownError: 'Неизвестная ошибка',
    connectionLost: 'Соединение потеряно',
    reconnecting: 'Переподключение...',
  },
} as const;

// Type-safe translation getter
export function t(key: string): string {
  const keys = key.split('.');
  let result: unknown = translations;
  
  for (const k of keys) {
    if (result && typeof result === 'object' && k in result) {
      result = (result as Record<string, unknown>)[k];
    } else {
      console.warn(`Translation not found: ${key}`);
      return key;
    }
  }
  
  return typeof result === 'string' ? result : key;
}

export default translations;
