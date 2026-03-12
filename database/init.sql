-- AuraTrade Database Initialization
-- Run automatically by Docker on first start

-- Seed default strategy settings
INSERT INTO strategy_settings (
    timeframe, rsi_period, rsi_oversold, rsi_overbought,
    fast_ma_period, slow_ma_period, ma_type,
    atr_period, atr_multiplier_sl, atr_multiplier_tp,
    risk_per_trade_pct, max_lot_size, daily_loss_limit_pct,
    max_open_trades, min_signal_strength, use_ml_filter,
    check_interval_seconds, updated_at
)
SELECT 'H1', 14, 30, 70, 20, 50, 'EMA', 14, 1.5, 2.5,
       1.0, 1.0, 5.0, 3, 50, true, 60, NOW()
WHERE NOT EXISTS (SELECT 1 FROM strategy_settings LIMIT 1);

-- Seed initial bot status
INSERT INTO bot_status (status, updated_at)
SELECT 'stopped', NOW()
WHERE NOT EXISTS (SELECT 1 FROM bot_status LIMIT 1);
