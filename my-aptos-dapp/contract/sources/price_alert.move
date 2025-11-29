module price_alert_addr::price_alert {
    use std::string::String;
    use aptos_framework::object::{Self, ExtendRef};
    use aptos_framework::account;
    use aptos_framework::timestamp;

    /// Alert structure
    struct Alert has store, copy, drop {
        alert_id: u64,
        user: address,
        token: String,
        operator: u8, // 0 = less than, 1 = greater than, 2 = equal
        target_price: u64,
        message: String,
        is_active: bool,
        created_at: u64,
    }

    /// Alert manager to store all alerts
    struct AlertManager has key {
        extend_ref: ExtendRef,
        alerts: vector<Alert>,
        next_alert_id: u64,
    }

    const ALERT_MANAGER_SEED: vector<u8> = b"price_alert_manager";
    const OPERATOR_LT: u8 = 0;
    const OPERATOR_GT: u8 = 1;
    const OPERATOR_EQ: u8 = 2;

    /// Error codes
    const ERR_ALERT_NOT_FOUND: u64 = 1;
    const ERR_INVALID_OPERATOR: u64 = 2;
    const ERR_ALERT_INACTIVE: u64 = 3;

    /// Initialize the alert manager
    fun init_module(sender: &signer) {
        let constructor_ref = &object::create_named_object(sender, ALERT_MANAGER_SEED);
        move_to(&object::generate_signer(constructor_ref), AlertManager {
            extend_ref: object::generate_extend_ref(constructor_ref),
            alerts: vector::empty(),
            next_alert_id: 1,
        });
    }

    /// Create a price alert (less than)
    public entry fun create_alert_lt(
        sender: &signer,
        token: String,
        target_price: u64,
        message: String,
    ) acquires AlertManager {
        create_alert_internal(sender, token, OPERATOR_LT, target_price, message);
    }

    /// Create a price alert (greater than)
    public entry fun create_alert_gt(
        sender: &signer,
        token: String,
        target_price: u64,
        message: String,
    ) acquires AlertManager {
        create_alert_internal(sender, token, OPERATOR_GT, target_price, message);
    }

    /// Create a price alert (equal)
    public entry fun create_alert_eq(
        sender: &signer,
        token: String,
        target_price: u64,
        message: String,
    ) acquires AlertManager {
        create_alert_internal(sender, token, OPERATOR_EQ, target_price, message);
    }

    /// Internal function to create an alert
    fun create_alert_internal(
        sender: &signer,
        token: String,
        operator: u8,
        target_price: u64,
        message: String,
    ) acquires AlertManager {
        let user = account::get_signer_capability_address(&signer::signer_capability_of(sender));
        let manager = borrow_global_mut<AlertManager>(get_manager_address());
        
        let alert = Alert {
            alert_id: manager.next_alert_id,
            user,
            token,
            operator,
            target_price,
            message,
            is_active: true,
            created_at: timestamp::now_seconds(),
        };
        
        vector::push_back(&mut manager.alerts, alert);
        manager.next_alert_id = manager.next_alert_id + 1;
    }

    /// Deactivate an alert
    public entry fun deactivate_alert(
        _sender: &signer,
        alert_id: u64,
    ) acquires AlertManager {
        let manager = borrow_global_mut<AlertManager>(get_manager_address());
        let i = 0;
        let len = vector::length(&manager.alerts);
        
        while (i < len) {
            let alert = vector::borrow_mut(&mut manager.alerts, i);
            if (alert.alert_id == alert_id) {
                alert.is_active = false;
                return
            };
            i = i + 1;
        };
        
        abort ERR_ALERT_NOT_FOUND
    }

    /// Get total number of alerts
    #[view]
    public fun get_alert_count(): u64 acquires AlertManager {
        let manager = borrow_global<AlertManager>(get_manager_address());
        vector::length(&manager.alerts)
    }

    /// Get all active alerts for a user
    #[view]
    public fun get_user_active_alerts(user: address): vector<Alert> acquires AlertManager {
        let manager = borrow_global<AlertManager>(get_manager_address());
        let user_alerts = vector::empty();
        let i = 0;
        let len = vector::length(&manager.alerts);
        
        while (i < len) {
            let alert = *vector::borrow(&manager.alerts, i);
            if (alert.user == user && alert.is_active) {
                vector::push_back(&mut user_alerts, alert);
            };
            i = i + 1;
        };
        
        user_alerts
    }

    /// Get a specific alert by ID
    #[view]
    public fun get_alert(alert_id: u64): Alert acquires AlertManager {
        let manager = borrow_global<AlertManager>(get_manager_address());
        let i = 0;
        let len = vector::length(&manager.alerts);
        
        while (i < len) {
            let alert = *vector::borrow(&manager.alerts, i);
            if (alert.alert_id == alert_id) {
                return alert
            };
            i = i + 1;
        };
        
        abort ERR_ALERT_NOT_FOUND
    }

    /// Check if an alert should trigger (helper view function)
    #[view]
    public fun should_alert_trigger(alert_id: u64, current_price: u64): bool acquires AlertManager {
        let alert = get_alert(alert_id);
        assert!(alert.is_active, ERR_ALERT_INACTIVE);
        
        if (alert.operator == OPERATOR_LT) {
            current_price < alert.target_price
        } else if (alert.operator == OPERATOR_GT) {
            current_price > alert.target_price
        } else if (alert.operator == OPERATOR_EQ) {
            current_price == alert.target_price
        } else {
            abort ERR_INVALID_OPERATOR
        }
    }

    /// Helper function to get manager address
    fun get_manager_address(): address {
        object::create_object_address(&@price_alert_addr, ALERT_MANAGER_SEED)
    }

    // ======================== Unit Tests ========================

    #[test_only]
    public fun init_module_for_test(sender: &signer) {
        init_module(sender);
    }
}
