/// Unit Tests for Trade.apt
#[test_only]
module trade_apt::trade_apt_tests {
    use std::string::utf8;
    use std::signer;
    use aptos_framework::timestamp;
    use aptos_framework::account;
    use trade_apt::trade_apt;

    // Test accounts
    const ADMIN: address = @0x1;
    const USER1: address = @0x2;
    const USER2: address = @0x3;

    // ============================================================
    // Setup
    // ============================================================

    fun setup_test(aptos_framework: &signer, admin: &signer) {
        // Initialize timestamp for testing
        timestamp::set_time_has_started_for_testing(aptos_framework);
        timestamp::update_global_time_for_test(1000000);

        // Initialize protocol
        trade_apt::initialize(admin);
    }

    // ============================================================
    // Initialization Tests
    // ============================================================

    #[test(aptos_framework = @0x1, admin = @trade_apt)]
    fun test_initialize_success(aptos_framework: &signer, admin: &signer) {
        setup_test(aptos_framework, admin);
        
        // Verify protocol stats are initialized
        let (total_trades, total_volume, total_orders) = trade_apt::get_protocol_stats();
        assert!(total_trades == 0, 1);
        assert!(total_volume == 0, 2);
        assert!(total_orders == 0, 3);
    }

    #[test(aptos_framework = @0x1, admin = @trade_apt)]
    #[expected_failure(abort_code = 2)] // E_ALREADY_INITIALIZED
    fun test_initialize_twice_fails(aptos_framework: &signer, admin: &signer) {
        setup_test(aptos_framework, admin);
        
        // Try to initialize again - should fail
        trade_apt::initialize(admin);
    }

    // ============================================================
    // User Account Tests
    // ============================================================

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    fun test_init_user_account(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        // Initialize user account
        trade_apt::init_user_account(user);
        
        let user_addr = signer::address_of(user);
        let (trades, volume, created_at) = trade_apt::get_user_stats(user_addr);
        
        assert!(trades == 0, 1);
        assert!(volume == 0, 2);
        assert!(created_at > 0, 3);
    }

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    fun test_get_stats_nonexistent_user(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        // Get stats for user that hasn't initialized
        let user_addr = signer::address_of(user);
        let (trades, volume, created_at) = trade_apt::get_user_stats(user_addr);
        
        assert!(trades == 0, 1);
        assert!(volume == 0, 2);
        assert!(created_at == 0, 3);
    }

    // ============================================================
    // Conditional Order Tests
    // ============================================================

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    fun test_create_conditional_order(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        // Create order: Buy APT when price < $7
        trade_apt::create_conditional_order(
            user,
            utf8(b"USDC"),      // token_in
            utf8(b"APT"),       // token_out
            20_00000000,        // 20 USDC (8 decimals)
            2_00000000,         // min 2 APT out
            2,                  // CONDITION_PRICE_BELOW
            700000000,          // target price: $7.00
            86400,              // expires in 24 hours
        );
        
        // Verify order created
        let pending_count = trade_apt::get_pending_orders_count();
        assert!(pending_count == 1, 1);
        
        // Verify protocol stats updated
        let (_, _, total_orders) = trade_apt::get_protocol_stats();
        assert!(total_orders == 1, 2);
    }

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    #[expected_failure(abort_code = 4)] // E_INVALID_AMOUNT
    fun test_create_order_zero_amount_fails(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        trade_apt::create_conditional_order(
            user,
            utf8(b"USDC"),
            utf8(b"APT"),
            0,                  // Zero amount - should fail
            0,
            2,
            700000000,
            86400,
        );
    }

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    #[expected_failure(abort_code = 7)] // E_INVALID_CONDITION
    fun test_create_order_invalid_condition_fails(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        trade_apt::create_conditional_order(
            user,
            utf8(b"USDC"),
            utf8(b"APT"),
            20_00000000,
            2_00000000,
            5,                  // Invalid condition type
            700000000,
            86400,
        );
    }

    // ============================================================
    // Order Cancellation Tests
    // ============================================================

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    fun test_cancel_order(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        // Create order
        trade_apt::create_conditional_order(
            user,
            utf8(b"USDC"),
            utf8(b"APT"),
            20_00000000,
            2_00000000,
            2,
            700000000,
            86400,
        );
        
        // Cancel order (order_id = 1)
        trade_apt::cancel_order(user, 1);
        
        // Verify no pending orders
        let pending_count = trade_apt::get_pending_orders_count();
        assert!(pending_count == 0, 1);
    }

    #[test(aptos_framework = @0x1, admin = @trade_apt, user1 = @0x2, user2 = @0x3)]
    #[expected_failure(abort_code = 6)] // E_UNAUTHORIZED
    fun test_cancel_other_user_order_fails(
        aptos_framework: &signer, 
        admin: &signer, 
        user1: &signer, 
        user2: &signer
    ) {
        setup_test(aptos_framework, admin);
        
        // User1 creates order
        trade_apt::create_conditional_order(
            user1,
            utf8(b"USDC"),
            utf8(b"APT"),
            20_00000000,
            2_00000000,
            2,
            700000000,
            86400,
        );
        
        // User2 tries to cancel - should fail
        trade_apt::cancel_order(user2, 1);
    }

    // ============================================================
    // Alert Tests
    // ============================================================

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    fun test_create_alert(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        // Create alert: Notify when APT < $7
        trade_apt::create_alert(
            user,
            utf8(b"APT"),
            2,                  // CONDITION_PRICE_BELOW
            700000000,          // $7.00
        );
        
        // Alert created successfully (no assertion needed, just no error)
    }

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    fun test_cancel_alert(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        // Create and cancel alert
        trade_apt::create_alert(
            user,
            utf8(b"APT"),
            2,
            700000000,
        );
        
        trade_apt::cancel_alert(user, 1);
        // Alert cancelled successfully
    }

    // ============================================================
    // Order Execution Tests
    // ============================================================

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2, executor = @0x3)]
    fun test_execute_conditional_order(
        aptos_framework: &signer, 
        admin: &signer, 
        user: &signer, 
        executor: &signer
    ) {
        setup_test(aptos_framework, admin);
        
        // Create order: Buy when price < $7
        trade_apt::create_conditional_order(
            user,
            utf8(b"USDC"),
            utf8(b"APT"),
            20_00000000,
            0,                  // No minimum for test
            2,                  // CONDITION_PRICE_BELOW
            700000000,          // $7.00
            86400,
        );
        
        // Execute with price at $6.50 (condition met)
        trade_apt::execute_conditional_order(
            executor,
            1,                  // order_id
            650000000,          // current price: $6.50
        );
        
        // Verify order executed
        let pending_count = trade_apt::get_pending_orders_count();
        assert!(pending_count == 0, 1);
        
        // Verify user stats updated
        let user_addr = signer::address_of(user);
        let (trades, volume, _) = trade_apt::get_user_stats(user_addr);
        assert!(trades == 1, 2);
        assert!(volume == 20_00000000, 3);
    }

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2, executor = @0x3)]
    #[expected_failure(abort_code = 7)] // E_INVALID_CONDITION (condition not met)
    fun test_execute_order_condition_not_met(
        aptos_framework: &signer, 
        admin: &signer, 
        user: &signer, 
        executor: &signer
    ) {
        setup_test(aptos_framework, admin);
        
        // Create order: Buy when price < $7
        trade_apt::create_conditional_order(
            user,
            utf8(b"USDC"),
            utf8(b"APT"),
            20_00000000,
            0,
            2,                  // CONDITION_PRICE_BELOW
            700000000,          // $7.00
            86400,
        );
        
        // Try to execute with price at $8.00 (condition NOT met)
        trade_apt::execute_conditional_order(
            executor,
            1,
            800000000,          // $8.00 - above target
        );
    }

    // ============================================================
    // Multiple Orders Tests
    // ============================================================

    #[test(aptos_framework = @0x1, admin = @trade_apt, user = @0x2)]
    fun test_multiple_orders(aptos_framework: &signer, admin: &signer, user: &signer) {
        setup_test(aptos_framework, admin);
        
        // Create 3 orders
        trade_apt::create_conditional_order(
            user, utf8(b"USDC"), utf8(b"APT"), 10_00000000, 0, 2, 700000000, 86400,
        );
        trade_apt::create_conditional_order(
            user, utf8(b"USDC"), utf8(b"BTC"), 50_00000000, 0, 2, 3000000000000, 86400,
        );
        trade_apt::create_conditional_order(
            user, utf8(b"USDC"), utf8(b"ETH"), 30_00000000, 0, 1, 200000000000, 86400,
        );
        
        let pending_count = trade_apt::get_pending_orders_count();
        assert!(pending_count == 3, 1);
        
        // Cancel middle order
        trade_apt::cancel_order(user, 2);
        
        let pending_count = trade_apt::get_pending_orders_count();
        assert!(pending_count == 2, 2);
    }
}
