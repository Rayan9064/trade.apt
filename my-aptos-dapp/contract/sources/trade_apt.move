/// Trade.apt - DeFi Trading Assistant for Aptos
/// 
/// This module provides:
/// - Token swaps via DEX integration
/// - Conditional/limit orders
/// - Price alerts with on-chain events
/// - Portfolio tracking
module trade_apt::trade_apt {
    use std::string::{String, utf8};
    use std::signer;
    use std::vector;
    use aptos_framework::event;
    use aptos_framework::timestamp;

    // ============================================================
    // Error Codes
    // ============================================================
    
    const E_NOT_INITIALIZED: u64 = 1;
    const E_ALREADY_INITIALIZED: u64 = 2;
    const E_INSUFFICIENT_BALANCE: u64 = 3;
    const E_INVALID_AMOUNT: u64 = 4;
    const E_ORDER_NOT_FOUND: u64 = 5;
    const E_UNAUTHORIZED: u64 = 6;
    const E_INVALID_CONDITION: u64 = 7;
    const E_ORDER_EXPIRED: u64 = 8;
    const E_SLIPPAGE_EXCEEDED: u64 = 9;

    // ============================================================
    // Constants
    // ============================================================
    
    const CONDITION_PRICE_ABOVE: u8 = 1;
    const CONDITION_PRICE_BELOW: u8 = 2;
    const CONDITION_IMMEDIATE: u8 = 3;

    const ORDER_STATUS_PENDING: u8 = 1;
    const ORDER_STATUS_EXECUTED: u8 = 2;
    const ORDER_STATUS_CANCELLED: u8 = 3;
    const ORDER_STATUS_EXPIRED: u8 = 4;

    // ============================================================
    // Structs
    // ============================================================

    /// Global state for the Trade.apt protocol
    struct TradeAptState has key {
        total_trades: u64,
        total_volume_apt: u64,
        total_orders_created: u64,
        admin: address,
    }

    /// User's trading account
    struct UserAccount has key {
        orders: vector<u64>,
        total_trades: u64,
        total_volume: u64,
        created_at: u64,
    }

    /// Conditional Order structure
    struct ConditionalOrder has store, drop, copy {
        order_id: u64,
        owner: address,
        token_in: String,
        token_out: String,
        amount_in: u64,
        min_amount_out: u64,
        condition_type: u8,
        target_price: u64,  // Price in USD with 8 decimals
        status: u8,
        created_at: u64,
        expires_at: u64,
        executed_at: u64,
    }

    /// Storage for all conditional orders
    struct OrderBook has key {
        orders: vector<ConditionalOrder>,
        next_order_id: u64,
    }

    /// Price Alert structure
    struct PriceAlert has store, drop, copy {
        alert_id: u64,
        owner: address,
        token: String,
        condition_type: u8,
        target_price: u64,
        is_active: bool,
        created_at: u64,
        triggered_at: u64,
    }

    /// User's price alerts
    struct UserAlerts has key {
        alerts: vector<PriceAlert>,
        next_alert_id: u64,
    }

    // ============================================================
    // Events
    // ============================================================

    #[event]
    struct TradeExecutedEvent has drop, store {
        user: address,
        token_in: String,
        token_out: String,
        amount_in: u64,
        amount_out: u64,
        price: u64,
        timestamp: u64,
    }

    #[event]
    struct OrderCreatedEvent has drop, store {
        order_id: u64,
        user: address,
        token_in: String,
        token_out: String,
        amount_in: u64,
        condition_type: u8,
        target_price: u64,
        expires_at: u64,
    }

    #[event]
    struct OrderExecutedEvent has drop, store {
        order_id: u64,
        user: address,
        amount_in: u64,
        amount_out: u64,
        execution_price: u64,
        timestamp: u64,
    }

    #[event]
    struct OrderCancelledEvent has drop, store {
        order_id: u64,
        user: address,
        timestamp: u64,
    }

    #[event]
    struct AlertTriggeredEvent has drop, store {
        alert_id: u64,
        user: address,
        token: String,
        target_price: u64,
        current_price: u64,
        timestamp: u64,
    }

    #[event]
    struct AlertCreatedEvent has drop, store {
        alert_id: u64,
        user: address,
        token: String,
        condition_type: u8,
        target_price: u64,
    }

    // ============================================================
    // Initialization
    // ============================================================

    /// Initialize the Trade.apt protocol (called once by admin)
    public entry fun initialize(admin: &signer) {
        let admin_addr = signer::address_of(admin);
        
        assert!(!exists<TradeAptState>(admin_addr), E_ALREADY_INITIALIZED);

        move_to(admin, TradeAptState {
            total_trades: 0,
            total_volume_apt: 0,
            total_orders_created: 0,
            admin: admin_addr,
        });

        move_to(admin, OrderBook {
            orders: vector::empty(),
            next_order_id: 1,
        });
    }

    /// Initialize user account
    public entry fun init_user_account(user: &signer) {
        let user_addr = signer::address_of(user);
        
        if (!exists<UserAccount>(user_addr)) {
            move_to(user, UserAccount {
                orders: vector::empty(),
                total_trades: 0,
                total_volume: 0,
                created_at: timestamp::now_seconds(),
            });
        };

        if (!exists<UserAlerts>(user_addr)) {
            move_to(user, UserAlerts {
                alerts: vector::empty(),
                next_alert_id: 1,
            });
        };
    }

    // ============================================================
    // Trading Functions
    // ============================================================

    /// Execute an immediate swap (integrates with DEX)
    /// In production, this would call Liquidswap/PancakeSwap
    public entry fun execute_swap<TokenIn, TokenOut>(
        user: &signer,
        amount_in: u64,
        min_amount_out: u64,
    ) acquires TradeAptState, UserAccount {
        let user_addr = signer::address_of(user);
        
        assert!(amount_in > 0, E_INVALID_AMOUNT);
        
        // Ensure user account exists
        if (!exists<UserAccount>(user_addr)) {
            init_user_account(user);
        };

        // In production: Call DEX router here
        // For hackathon demo, we simulate the swap
        let amount_out = calculate_swap_output(amount_in);
        
        assert!(amount_out >= min_amount_out, E_SLIPPAGE_EXCEEDED);

        // Update user stats
        let user_account = borrow_global_mut<UserAccount>(user_addr);
        user_account.total_trades = user_account.total_trades + 1;
        user_account.total_volume = user_account.total_volume + amount_in;

        // Update global stats
        let state = borrow_global_mut<TradeAptState>(@trade_apt);
        state.total_trades = state.total_trades + 1;
        state.total_volume_apt = state.total_volume_apt + amount_in;

        // Emit event
        event::emit(TradeExecutedEvent {
            user: user_addr,
            token_in: utf8(b"APT"),
            token_out: utf8(b"USDC"),
            amount_in,
            amount_out,
            price: get_current_price(),
            timestamp: timestamp::now_seconds(),
        });
    }

    /// Create a conditional/limit order
    public entry fun create_conditional_order(
        user: &signer,
        token_in: String,
        token_out: String,
        amount_in: u64,
        min_amount_out: u64,
        condition_type: u8,
        target_price: u64,
        duration_seconds: u64,
    ) acquires OrderBook, UserAccount, TradeAptState {
        let user_addr = signer::address_of(user);
        
        assert!(amount_in > 0, E_INVALID_AMOUNT);
        assert!(
            condition_type == CONDITION_PRICE_ABOVE || 
            condition_type == CONDITION_PRICE_BELOW,
            E_INVALID_CONDITION
        );

        // Ensure user account exists
        if (!exists<UserAccount>(user_addr)) {
            init_user_account(user);
        };

        let order_book = borrow_global_mut<OrderBook>(@trade_apt);
        let order_id = order_book.next_order_id;
        let now = timestamp::now_seconds();

        let order = ConditionalOrder {
            order_id,
            owner: user_addr,
            token_in,
            token_out,
            amount_in,
            min_amount_out,
            condition_type,
            target_price,
            status: ORDER_STATUS_PENDING,
            created_at: now,
            expires_at: now + duration_seconds,
            executed_at: 0,
        };

        vector::push_back(&mut order_book.orders, order);
        order_book.next_order_id = order_id + 1;

        // Add order to user's list
        let user_account = borrow_global_mut<UserAccount>(user_addr);
        vector::push_back(&mut user_account.orders, order_id);

        // Update global stats
        let state = borrow_global_mut<TradeAptState>(@trade_apt);
        state.total_orders_created = state.total_orders_created + 1;

        // Emit event
        event::emit(OrderCreatedEvent {
            order_id,
            user: user_addr,
            token_in: utf8(b"APT"),
            token_out: utf8(b"USDC"),
            amount_in,
            condition_type,
            target_price,
            expires_at: now + duration_seconds,
        });
    }

    /// Cancel a pending order
    public entry fun cancel_order(
        user: &signer,
        order_id: u64,
    ) acquires OrderBook {
        let user_addr = signer::address_of(user);
        let order_book = borrow_global_mut<OrderBook>(@trade_apt);
        
        let (found, index) = find_order(&order_book.orders, order_id);
        assert!(found, E_ORDER_NOT_FOUND);

        let order = vector::borrow_mut(&mut order_book.orders, index);
        assert!(order.owner == user_addr, E_UNAUTHORIZED);
        assert!(order.status == ORDER_STATUS_PENDING, E_ORDER_NOT_FOUND);

        order.status = ORDER_STATUS_CANCELLED;

        event::emit(OrderCancelledEvent {
            order_id,
            user: user_addr,
            timestamp: timestamp::now_seconds(),
        });
    }

    /// Execute a conditional order (called by keeper/bot when conditions are met)
    public entry fun execute_conditional_order(
        executor: &signer,
        order_id: u64,
        current_price: u64,
    ) acquires OrderBook, UserAccount, TradeAptState {
        let order_book = borrow_global_mut<OrderBook>(@trade_apt);
        
        let (found, index) = find_order(&order_book.orders, order_id);
        assert!(found, E_ORDER_NOT_FOUND);

        let order = vector::borrow_mut(&mut order_book.orders, index);
        assert!(order.status == ORDER_STATUS_PENDING, E_ORDER_NOT_FOUND);
        
        let now = timestamp::now_seconds();
        assert!(now <= order.expires_at, E_ORDER_EXPIRED);

        // Check if condition is met
        let condition_met = if (order.condition_type == CONDITION_PRICE_BELOW) {
            current_price <= order.target_price
        } else {
            current_price >= order.target_price
        };
        
        assert!(condition_met, E_INVALID_CONDITION);

        // Calculate output amount
        let amount_out = calculate_swap_output(order.amount_in);
        assert!(amount_out >= order.min_amount_out, E_SLIPPAGE_EXCEEDED);

        // Update order status
        order.status = ORDER_STATUS_EXECUTED;
        order.executed_at = now;

        // Update user stats
        let user_account = borrow_global_mut<UserAccount>(order.owner);
        user_account.total_trades = user_account.total_trades + 1;
        user_account.total_volume = user_account.total_volume + order.amount_in;

        // Update global stats
        let state = borrow_global_mut<TradeAptState>(@trade_apt);
        state.total_trades = state.total_trades + 1;
        state.total_volume_apt = state.total_volume_apt + order.amount_in;

        event::emit(OrderExecutedEvent {
            order_id,
            user: order.owner,
            amount_in: order.amount_in,
            amount_out,
            execution_price: current_price,
            timestamp: now,
        });
    }

    // ============================================================
    // Alert Functions
    // ============================================================

    /// Create a price alert
    public entry fun create_alert(
        user: &signer,
        token: String,
        condition_type: u8,
        target_price: u64,
    ) acquires UserAlerts {
        let user_addr = signer::address_of(user);
        
        assert!(
            condition_type == CONDITION_PRICE_ABOVE || 
            condition_type == CONDITION_PRICE_BELOW,
            E_INVALID_CONDITION
        );

        if (!exists<UserAlerts>(user_addr)) {
            move_to(user, UserAlerts {
                alerts: vector::empty(),
                next_alert_id: 1,
            });
        };

        let user_alerts = borrow_global_mut<UserAlerts>(user_addr);
        let alert_id = user_alerts.next_alert_id;

        let alert = PriceAlert {
            alert_id,
            owner: user_addr,
            token,
            condition_type,
            target_price,
            is_active: true,
            created_at: timestamp::now_seconds(),
            triggered_at: 0,
        };

        vector::push_back(&mut user_alerts.alerts, alert);
        user_alerts.next_alert_id = alert_id + 1;

        event::emit(AlertCreatedEvent {
            alert_id,
            user: user_addr,
            token: utf8(b"APT"),
            condition_type,
            target_price,
        });
    }

    /// Trigger an alert (called by keeper when conditions are met)
    public entry fun trigger_alert(
        _executor: &signer,
        user_addr: address,
        alert_id: u64,
        current_price: u64,
    ) acquires UserAlerts {
        let user_alerts = borrow_global_mut<UserAlerts>(user_addr);
        
        let (found, index) = find_alert(&user_alerts.alerts, alert_id);
        assert!(found, E_ORDER_NOT_FOUND);

        let alert = vector::borrow_mut(&mut user_alerts.alerts, index);
        assert!(alert.is_active, E_ORDER_NOT_FOUND);

        // Check condition
        let condition_met = if (alert.condition_type == CONDITION_PRICE_BELOW) {
            current_price <= alert.target_price
        } else {
            current_price >= alert.target_price
        };

        assert!(condition_met, E_INVALID_CONDITION);

        alert.is_active = false;
        alert.triggered_at = timestamp::now_seconds();

        event::emit(AlertTriggeredEvent {
            alert_id,
            user: user_addr,
            token: alert.token,
            target_price: alert.target_price,
            current_price,
            timestamp: timestamp::now_seconds(),
        });
    }

    /// Cancel an alert
    public entry fun cancel_alert(
        user: &signer,
        alert_id: u64,
    ) acquires UserAlerts {
        let user_addr = signer::address_of(user);
        let user_alerts = borrow_global_mut<UserAlerts>(user_addr);
        
        let (found, index) = find_alert(&user_alerts.alerts, alert_id);
        assert!(found, E_ORDER_NOT_FOUND);

        let alert = vector::borrow_mut(&mut user_alerts.alerts, index);
        assert!(alert.owner == user_addr, E_UNAUTHORIZED);
        
        alert.is_active = false;
    }

    // ============================================================
    // View Functions
    // ============================================================

    #[view]
    public fun get_user_stats(user_addr: address): (u64, u64, u64) acquires UserAccount {
        if (!exists<UserAccount>(user_addr)) {
            return (0, 0, 0)
        };
        let account = borrow_global<UserAccount>(user_addr);
        (account.total_trades, account.total_volume, account.created_at)
    }

    #[view]
    public fun get_protocol_stats(): (u64, u64, u64) acquires TradeAptState {
        let state = borrow_global<TradeAptState>(@trade_apt);
        (state.total_trades, state.total_volume_apt, state.total_orders_created)
    }

    #[view]
    public fun get_pending_orders_count(): u64 acquires OrderBook {
        let order_book = borrow_global<OrderBook>(@trade_apt);
        let count = 0u64;
        let len = vector::length(&order_book.orders);
        let i = 0;
        while (i < len) {
            let order = vector::borrow(&order_book.orders, i);
            if (order.status == ORDER_STATUS_PENDING) {
                count = count + 1;
            };
            i = i + 1;
        };
        count
    }

    // ============================================================
    // Helper Functions
    // ============================================================

    fun find_order(orders: &vector<ConditionalOrder>, order_id: u64): (bool, u64) {
        let len = vector::length(orders);
        let i = 0;
        while (i < len) {
            let order = vector::borrow(orders, i);
            if (order.order_id == order_id) {
                return (true, i)
            };
            i = i + 1;
        };
        (false, 0)
    }

    fun find_alert(alerts: &vector<PriceAlert>, alert_id: u64): (bool, u64) {
        let len = vector::length(alerts);
        let i = 0;
        while (i < len) {
            let alert = vector::borrow(alerts, i);
            if (alert.alert_id == alert_id) {
                return (true, i)
            };
            i = i + 1;
        };
        (false, 0)
    }

    /// Simulate swap calculation (replace with actual DEX integration)
    fun calculate_swap_output(amount_in: u64): u64 {
        // Simplified: 1 APT = ~8.5 USDC (with 0.3% fee)
        // In production, query DEX for actual rate
        (amount_in * 850 * 997) / (100 * 1000)
    }

    /// Get current price (placeholder - integrate with oracle)
    fun get_current_price(): u64 {
        // Return price with 8 decimals (e.g., 850000000 = $8.50)
        // In production, integrate with Pyth or Switchboard oracle
        850000000
    }
}
