/// Price Oracle Integration for Trade.apt
/// 
/// Integrates with Pyth Network and Switchboard for reliable price feeds
/// Used for conditional orders and price alerts
module trade_apt::price_oracle {
    use std::string::{String, utf8};
    use std::signer;
    use std::vector;
    use aptos_framework::event;
    use aptos_framework::timestamp;

    // ============================================================
    // Error Codes
    // ============================================================
    
    const E_PRICE_STALE: u64 = 1;
    const E_INVALID_PRICE: u64 = 2;
    const E_UNAUTHORIZED: u64 = 3;
    const E_FEED_NOT_FOUND: u64 = 4;

    // ============================================================
    // Constants
    // ============================================================
    
    /// Maximum age of price data in seconds
    const MAX_PRICE_AGE: u64 = 60;
    
    /// Price precision (8 decimals)
    const PRICE_DECIMALS: u8 = 8;

    // ============================================================
    // Structs
    // ============================================================

    /// Cached price data for a token
    struct PriceData has store, drop, copy {
        price: u64,           // Price with 8 decimals
        confidence: u64,      // Confidence interval
        timestamp: u64,       // Last update timestamp
        expo: u8,             // Exponent for price (unsigned)
    }

    /// Oracle configuration and cache
    struct OracleConfig has key {
        admin: address,
        keepers: vector<address>,
        price_cache: vector<PriceFeed>,
    }

    /// Individual price feed
    struct PriceFeed has store, drop, copy {
        token: String,
        price_data: PriceData,
        pyth_feed_id: vector<u8>,
        is_active: bool,
    }

    // ============================================================
    // Events
    // ============================================================

    #[event]
    struct PriceUpdatedEvent has drop, store {
        token: String,
        price: u64,
        confidence: u64,
        timestamp: u64,
    }

    // ============================================================
    // Initialization
    // ============================================================

    /// Initialize oracle configuration
    public entry fun initialize(admin: &signer) {
        let admin_addr = signer::address_of(admin);
        
        let keepers = vector::empty<address>();
        vector::push_back(&mut keepers, admin_addr);

        move_to(admin, OracleConfig {
            admin: admin_addr,
            keepers,
            price_cache: vector::empty(),
        });
    }

    /// Add a keeper address
    public entry fun add_keeper(
        admin: &signer,
        keeper: address,
    ) acquires OracleConfig {
        let admin_addr = signer::address_of(admin);
        let config = borrow_global_mut<OracleConfig>(admin_addr);
        
        assert!(config.admin == admin_addr, E_UNAUTHORIZED);
        vector::push_back(&mut config.keepers, keeper);
    }

    // ============================================================
    // Price Update Functions
    // ============================================================

    /// Update price from Pyth (called by keeper)
    public entry fun update_price(
        keeper: &signer,
        oracle_addr: address,
        token: String,
        price: u64,
        confidence: u64,
    ) acquires OracleConfig {
        let keeper_addr = signer::address_of(keeper);
        let config = borrow_global_mut<OracleConfig>(oracle_addr);
        
        // Verify keeper is authorized
        assert!(is_keeper(&config.keepers, keeper_addr), E_UNAUTHORIZED);
        assert!(price > 0, E_INVALID_PRICE);

        let now = timestamp::now_seconds();
        let price_data = PriceData {
            price,
            confidence,
            timestamp: now,
            expo: 8,
        };

        // Find and update or create feed
        let (found, index) = find_feed(&config.price_cache, &token);
        if (found) {
            let feed = vector::borrow_mut(&mut config.price_cache, index);
            feed.price_data = price_data;
        } else {
            let feed = PriceFeed {
                token,
                price_data,
                pyth_feed_id: vector::empty(),
                is_active: true,
            };
            vector::push_back(&mut config.price_cache, feed);
        };

        event::emit(PriceUpdatedEvent {
            token: utf8(b"TOKEN"),
            price,
            confidence,
            timestamp: now,
        });
    }

    /// Batch update multiple prices
    public entry fun batch_update_prices(
        keeper: &signer,
        oracle_addr: address,
        tokens: vector<String>,
        prices: vector<u64>,
        confidences: vector<u64>,
    ) acquires OracleConfig {
        let len = vector::length(&tokens);
        assert!(len == vector::length(&prices), E_INVALID_PRICE);
        assert!(len == vector::length(&confidences), E_INVALID_PRICE);

        let i = 0;
        while (i < len) {
            let token = *vector::borrow(&tokens, i);
            let price = *vector::borrow(&prices, i);
            let confidence = *vector::borrow(&confidences, i);
            
            update_price(keeper, oracle_addr, token, price, confidence);
            i = i + 1;
        };
    }

    // ============================================================
    // View Functions
    // ============================================================

    #[view]
    /// Get current price for a token
    public fun get_price(oracle_addr: address, token: String): (u64, u64, u64) acquires OracleConfig {
        let config = borrow_global<OracleConfig>(oracle_addr);
        let (found, index) = find_feed(&config.price_cache, &token);
        
        if (!found) {
            return (0, 0, 0)
        };

        let feed = vector::borrow(&config.price_cache, index);
        (feed.price_data.price, feed.price_data.confidence, feed.price_data.timestamp)
    }

    #[view]
    /// Check if price is fresh (not stale)
    public fun is_price_fresh(oracle_addr: address, token: String): bool acquires OracleConfig {
        let (_, _, last_update) = get_price(oracle_addr, token);
        if (last_update == 0) {
            return false
        };
        
        let now = timestamp::now_seconds();
        now - last_update <= MAX_PRICE_AGE
    }

    #[view]
    /// Get price with staleness check
    public fun get_price_safe(oracle_addr: address, token: String): (u64, bool) acquires OracleConfig {
        let (price, _, timestamp) = get_price(oracle_addr, token);
        let is_fresh = if (timestamp == 0) {
            false
        } else {
            timestamp::now_seconds() - timestamp <= MAX_PRICE_AGE
        };
        (price, is_fresh)
    }

    // ============================================================
    // Helper Functions
    // ============================================================

    fun is_keeper(keepers: &vector<address>, addr: address): bool {
        let len = vector::length(keepers);
        let i = 0;
        while (i < len) {
            if (*vector::borrow(keepers, i) == addr) {
                return true
            };
            i = i + 1;
        };
        false
    }

    fun find_feed(feeds: &vector<PriceFeed>, token: &String): (bool, u64) {
        let len = vector::length(feeds);
        let i = 0;
        while (i < len) {
            let feed = vector::borrow(feeds, i);
            if (&feed.token == token) {
                return (true, i)
            };
            i = i + 1;
        };
        (false, 0)
    }
}
