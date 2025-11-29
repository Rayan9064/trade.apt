module user_portfolio_addr::user_portfolio {
    use std::string::String;
    use aptos_framework::object::{Self, ExtendRef};
    use aptos_framework::account;

    /// Token position in portfolio
    struct TokenPosition has store, copy, drop {
        token: String,
        amount: u64,
        average_entry_price: u64,
        total_value_usd: u64,
    }

    /// User portfolio
    struct Portfolio has key {
        user: address,
        total_value_usd: u64,
        positions: vector<TokenPosition>,
    }

    /// Portfolio manager to store all user portfolios
    struct PortfolioManager has key {
        extend_ref: ExtendRef,
        portfolios: vector<Portfolio>,
    }

    const PORTFOLIO_MANAGER_SEED: vector<u8> = b"user_portfolio_manager";

    /// Error codes
    const ERR_PORTFOLIO_NOT_FOUND: u64 = 1;
    const ERR_POSITION_NOT_FOUND: u64 = 2;
    const ERR_INVALID_AMOUNT: u64 = 3;

    /// Initialize the portfolio manager
    fun init_module(sender: &signer) {
        let constructor_ref = &object::create_named_object(sender, PORTFOLIO_MANAGER_SEED);
        move_to(&object::generate_signer(constructor_ref), PortfolioManager {
            extend_ref: object::generate_extend_ref(constructor_ref),
            portfolios: vector::empty(),
        });
    }

    /// Initialize a portfolio for a user
    public entry fun initialize_portfolio(sender: &signer) acquires PortfolioManager {
        let user = account::get_signer_capability_address(&signer::signer_capability_of(sender));
        let manager = borrow_global_mut<PortfolioManager>(get_manager_address());
        
        // Check if portfolio already exists
        let i = 0;
        let len = vector::length(&manager.portfolios);
        while (i < len) {
            let portfolio = vector::borrow(&manager.portfolios, i);
            assert!(portfolio.user != user, ERR_PORTFOLIO_NOT_FOUND);
            i = i + 1;
        };
        
        let portfolio = Portfolio {
            user,
            total_value_usd: 0,
            positions: vector::empty(),
        };
        
        vector::push_back(&mut manager.portfolios, portfolio);
    }

    /// Add or update a position in the portfolio
    public entry fun update_position(
        sender: &signer,
        token: String,
        amount: u64,
        price: u64,
    ) acquires PortfolioManager {
        let user = account::get_signer_capability_address(&signer::signer_capability_of(sender));
        assert!(amount > 0, ERR_INVALID_AMOUNT);
        
        let manager = borrow_global_mut<PortfolioManager>(get_manager_address());
        let i = 0;
        let len = vector::length(&manager.portfolios);
        
        while (i < len) {
            let portfolio = vector::borrow_mut(&mut manager.portfolios, i);
            if (portfolio.user == user) {
                update_position_internal(portfolio, token, amount, price);
                return
            };
            i = i + 1;
        };
        
        abort ERR_PORTFOLIO_NOT_FOUND
    }

    /// Internal function to update a position
    fun update_position_internal(
        portfolio: &mut Portfolio,
        token: String,
        amount: u64,
        price: u64,
    ) {
        let j = 0;
        let pos_len = vector::length(&portfolio.positions);
        
        // Check if position already exists
        while (j < pos_len) {
            let position = vector::borrow_mut(&mut portfolio.positions, j);
            if (position.token == token) {
                // Update existing position
                let new_value = amount * price;
                let old_total = position.amount * position.average_entry_price;
                let new_total = old_total + new_value;
                position.amount = position.amount + amount;
                position.average_entry_price = if (position.amount > 0) {
                    new_total / position.amount
                } else {
                    0
                };
                position.total_value_usd = position.amount * price;
                return
            };
            j = j + 1;
        };
        
        // Add new position if not found
        let new_position = TokenPosition {
            token,
            amount,
            average_entry_price: price,
            total_value_usd: amount * price,
        };
        vector::push_back(&mut portfolio.positions, new_position);
    }

    /// Remove a position from the portfolio
    public entry fun remove_position(
        sender: &signer,
        token: String,
    ) acquires PortfolioManager {
        let user = account::get_signer_capability_address(&signer::signer_capability_of(sender));
        let manager = borrow_global_mut<PortfolioManager>(get_manager_address());
        let i = 0;
        let len = vector::length(&manager.portfolios);
        
        while (i < len) {
            let portfolio = vector::borrow_mut(&mut manager.portfolios, i);
            if (portfolio.user == user) {
                let j = 0;
                let pos_len = vector::length(&portfolio.positions);
                while (j < pos_len) {
                    let position = vector::borrow(&portfolio.positions, j);
                    if (position.token == token) {
                        vector::remove(&mut portfolio.positions, j);
                        return
                    };
                    j = j + 1;
                };
                abort ERR_POSITION_NOT_FOUND
            };
            i = i + 1;
        };
        
        abort ERR_PORTFOLIO_NOT_FOUND
    }

    /// Get user portfolio
    #[view]
    public fun get_portfolio(user: address): Portfolio acquires PortfolioManager {
        let manager = borrow_global<PortfolioManager>(get_manager_address());
        let i = 0;
        let len = vector::length(&manager.portfolios);
        
        while (i < len) {
            let portfolio = *vector::borrow(&manager.portfolios, i);
            if (portfolio.user == user) {
                return portfolio
            };
            i = i + 1;
        };
        
        abort ERR_PORTFOLIO_NOT_FOUND
    }

    /// Get specific position in user's portfolio
    #[view]
    public fun get_position(user: address, token: String): TokenPosition acquires PortfolioManager {
        let portfolio = get_portfolio(user);
        let i = 0;
        let len = vector::length(&portfolio.positions);
        
        while (i < len) {
            let position = *vector::borrow(&portfolio.positions, i);
            if (position.token == token) {
                return position
            };
            i = i + 1;
        };
        
        abort ERR_POSITION_NOT_FOUND
    }

    /// Get total portfolio value
    #[view]
    public fun get_portfolio_value(user: address): u64 acquires PortfolioManager {
        let portfolio = get_portfolio(user);
        let total: u64 = 0;
        let i = 0;
        let len = vector::length(&portfolio.positions);
        
        while (i < len) {
            let position = vector::borrow(&portfolio.positions, i);
            total = total + position.total_value_usd;
            i = i + 1;
        };
        
        total
    }

    /// Helper function to get manager address
    fun get_manager_address(): address {
        object::create_object_address(&@user_portfolio_addr, PORTFOLIO_MANAGER_SEED)
    }

    // ======================== Unit Tests ========================

    #[test_only]
    public fun init_module_for_test(sender: &signer) {
        init_module(sender);
    }
}
