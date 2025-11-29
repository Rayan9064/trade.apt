module trade_registry_addr::trade_registry {
    use std::string::String;
    use aptos_framework::object::{Self, ExtendRef};
    use aptos_framework::account;
    use aptos_framework::timestamp;

    /// Trade record structure
    struct Trade has store, copy, drop {
        trade_id: u64,
        user: address,
        action: u8, // 0 = buy, 1 = sell, 2 = swap
        token_from: String,
        token_to: String,
        amount_usd: u64,
        executed_price: u64,
        tokens_received: u64,
        timestamp: u64,
    }

    /// Registry to store all trades
    struct TradeRegistry has key {
        extend_ref: ExtendRef,
        trades: vector<Trade>,
        next_trade_id: u64,
    }

    const TRADE_REGISTRY_SEED: vector<u8> = b"trade_registry";
    const ACTION_BUY: u8 = 0;
    const ACTION_SELL: u8 = 1;
    const ACTION_SWAP: u8 = 2;

    /// Error codes
    const ERR_REGISTRY_NOT_INITIALIZED: u64 = 1;
    const ERR_INVALID_ACTION: u64 = 2;

    /// Initialize the trade registry (called once at deployment)
    fun init_module(sender: &signer) {
        let constructor_ref = &object::create_named_object(sender, TRADE_REGISTRY_SEED);
        move_to(&object::generate_signer(constructor_ref), TradeRegistry {
            extend_ref: object::generate_extend_ref(constructor_ref),
            trades: vector::empty(),
            next_trade_id: 1,
        });
    }

    /// Record a buy trade
    public entry fun record_buy_trade(
        sender: &signer,
        token_from: String,
        token_to: String,
        amount_usd: u64,
        executed_price: u64,
        tokens_received: u64,
    ) acquires TradeRegistry {
        record_trade_internal(sender, ACTION_BUY, token_from, token_to, amount_usd, executed_price, tokens_received);
    }

    /// Record a sell trade
    public entry fun record_sell_trade(
        sender: &signer,
        token_from: String,
        token_to: String,
        amount_usd: u64,
        executed_price: u64,
        tokens_received: u64,
    ) acquires TradeRegistry {
        record_trade_internal(sender, ACTION_SELL, token_from, token_to, amount_usd, executed_price, tokens_received);
    }

    /// Record a swap trade
    public entry fun record_swap_trade(
        sender: &signer,
        token_from: String,
        token_to: String,
        amount_usd: u64,
        executed_price: u64,
        tokens_received: u64,
    ) acquires TradeRegistry {
        record_trade_internal(sender, ACTION_SWAP, token_from, token_to, amount_usd, executed_price, tokens_received);
    }

    /// Internal function to record a trade
    fun record_trade_internal(
        sender: &signer,
        action: u8,
        token_from: String,
        token_to: String,
        amount_usd: u64,
        executed_price: u64,
        tokens_received: u64,
    ) acquires TradeRegistry {
        let user = account::get_signer_capability_address(&signer::signer_capability_of(sender));
        let registry = borrow_global_mut<TradeRegistry>(get_registry_address());
        
        let trade = Trade {
            trade_id: registry.next_trade_id,
            user,
            action,
            token_from,
            token_to,
            amount_usd,
            executed_price,
            tokens_received,
            timestamp: timestamp::now_seconds(),
        };
        
        vector::push_back(&mut registry.trades, trade);
        registry.next_trade_id = registry.next_trade_id + 1;
    }

    /// Get total number of trades
    #[view]
    public fun get_trade_count(): u64 acquires TradeRegistry {
        let registry = borrow_global<TradeRegistry>(get_registry_address());
        vector::length(&registry.trades)
    }

    /// Get all trades for a user
    #[view]
    public fun get_user_trades(user: address): vector<Trade> acquires TradeRegistry {
        let registry = borrow_global<TradeRegistry>(get_registry_address());
        let user_trades = vector::empty();
        let i = 0;
        let len = vector::length(&registry.trades);
        
        while (i < len) {
            let trade = *vector::borrow(&registry.trades, i);
            if (trade.user == user) {
                vector::push_back(&mut user_trades, trade);
            };
            i = i + 1;
        };
        
        user_trades
    }

    /// Get a specific trade by ID
    #[view]
    public fun get_trade(trade_id: u64): Trade acquires TradeRegistry {
        let registry = borrow_global<TradeRegistry>(get_registry_address());
        let i = 0;
        let len = vector::length(&registry.trades);
        
        while (i < len) {
            let trade = *vector::borrow(&registry.trades, i);
            if (trade.trade_id == trade_id) {
                return trade
            };
            i = i + 1;
        };
        
        abort ERR_REGISTRY_NOT_INITIALIZED
    }

    /// Helper function to get registry address
    fun get_registry_address(): address {
        object::create_object_address(&@trade_registry_addr, TRADE_REGISTRY_SEED)
    }

    // ======================== Unit Tests ========================

    #[test_only]
    public fun init_module_for_test(sender: &signer) {
        init_module(sender);
    }
}
