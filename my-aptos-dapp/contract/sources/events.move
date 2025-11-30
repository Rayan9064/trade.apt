/// Events Module for Trade.apt
/// 
/// Centralized event definitions for cross-module use
/// Enables frontend to subscribe and react to on-chain events
module trade_apt::events {
    use std::string::String;
    use aptos_framework::event;

    // ============================================================
    // Protocol Events
    // ============================================================

    #[event]
    struct ProtocolInitializedEvent has drop, store {
        admin: address,
        timestamp: u64,
    }

    #[event]
    struct ProtocolPausedEvent has drop, store {
        admin: address,
        reason: String,
        timestamp: u64,
    }

    #[event]
    struct ProtocolUnpausedEvent has drop, store {
        admin: address,
        timestamp: u64,
    }

    // ============================================================
    // User Events
    // ============================================================

    #[event]
    struct UserRegisteredEvent has drop, store {
        user: address,
        timestamp: u64,
    }

    #[event]
    struct UserSettingsUpdatedEvent has drop, store {
        user: address,
        setting_key: String,
        timestamp: u64,
    }

    // ============================================================
    // Trading Events
    // ============================================================

    #[event]
    struct MarketOrderEvent has drop, store {
        user: address,
        order_type: u8,  // 1 = buy, 2 = sell
        token_in: String,
        token_out: String,
        amount_in: u64,
        amount_out: u64,
        price: u64,
        slippage_bps: u64,
        timestamp: u64,
    }

    #[event]
    struct LimitOrderCreatedEvent has drop, store {
        order_id: u64,
        user: address,
        token_in: String,
        token_out: String,
        amount_in: u64,
        limit_price: u64,
        expires_at: u64,
        timestamp: u64,
    }

    #[event]
    struct LimitOrderFilledEvent has drop, store {
        order_id: u64,
        user: address,
        amount_in: u64,
        amount_out: u64,
        fill_price: u64,
        timestamp: u64,
    }

    #[event]
    struct LimitOrderCancelledEvent has drop, store {
        order_id: u64,
        user: address,
        reason: String,
        timestamp: u64,
    }

    #[event]
    struct StopLossTriggeredEvent has drop, store {
        order_id: u64,
        user: address,
        trigger_price: u64,
        execution_price: u64,
        amount_sold: u64,
        timestamp: u64,
    }

    #[event]
    struct TakeProfitTriggeredEvent has drop, store {
        order_id: u64,
        user: address,
        trigger_price: u64,
        execution_price: u64,
        amount_sold: u64,
        profit_usd: u64,
        timestamp: u64,
    }

    // ============================================================
    // Alert Events
    // ============================================================

    #[event]
    struct PriceAlertCreatedEvent has drop, store {
        alert_id: u64,
        user: address,
        token: String,
        condition: u8,  // 1 = above, 2 = below
        target_price: u64,
        timestamp: u64,
    }

    #[event]
    struct PriceAlertTriggeredEvent has drop, store {
        alert_id: u64,
        user: address,
        token: String,
        target_price: u64,
        actual_price: u64,
        timestamp: u64,
    }

    #[event]
    struct PriceAlertDeletedEvent has drop, store {
        alert_id: u64,
        user: address,
        timestamp: u64,
    }

    // ============================================================
    // Portfolio Events
    // ============================================================

    #[event]
    struct DepositEvent has drop, store {
        user: address,
        token: String,
        amount: u64,
        timestamp: u64,
    }

    #[event]
    struct WithdrawEvent has drop, store {
        user: address,
        token: String,
        amount: u64,
        timestamp: u64,
    }

    #[event]
    struct PortfolioRebalanceEvent has drop, store {
        user: address,
        trades_executed: u64,
        total_value_before: u64,
        total_value_after: u64,
        timestamp: u64,
    }

    // ============================================================
    // Emit Functions (for cross-module use)
    // ============================================================

    public fun emit_market_order(
        user: address,
        order_type: u8,
        token_in: String,
        token_out: String,
        amount_in: u64,
        amount_out: u64,
        price: u64,
        slippage_bps: u64,
        timestamp: u64,
    ) {
        event::emit(MarketOrderEvent {
            user,
            order_type,
            token_in,
            token_out,
            amount_in,
            amount_out,
            price,
            slippage_bps,
            timestamp,
        });
    }

    public fun emit_limit_order_created(
        order_id: u64,
        user: address,
        token_in: String,
        token_out: String,
        amount_in: u64,
        limit_price: u64,
        expires_at: u64,
        timestamp: u64,
    ) {
        event::emit(LimitOrderCreatedEvent {
            order_id,
            user,
            token_in,
            token_out,
            amount_in,
            limit_price,
            expires_at,
            timestamp,
        });
    }

    public fun emit_price_alert_triggered(
        alert_id: u64,
        user: address,
        token: String,
        target_price: u64,
        actual_price: u64,
        timestamp: u64,
    ) {
        event::emit(PriceAlertTriggeredEvent {
            alert_id,
            user,
            token,
            target_price,
            actual_price,
            timestamp,
        });
    }
}
