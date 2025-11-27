const std = @import("std");

// =============================================================================
// Payment Service - Example for Mocking External Dependencies
// =============================================================================
// This example demonstrates functions that can be mocked at the FFI layer.
// Each function represents an "external service" that we want to mock in tests.

// =============================================================================
// Status Codes
// =============================================================================

pub const PaymentStatus = enum(i32) {
    Success = 0,
    GatewayTimeout = -1,
    GatewayDeclined = -2,
    FraudDetected = -3,
    InsufficientInventory = -4,
    InvalidAmount = -5,
};

// =============================================================================
// External Service Calls (these are the functions we mock in tests)
// =============================================================================

/// Simulates calling an external payment gateway
/// Returns: 1 = approved, 0 = declined, -1 = timeout/error
export fn call_payment_gateway(amount_cents: i32, card_token: [*:0]const u8) i32 {
    // In production, this would make an HTTP call to Stripe/PayPal/etc.
    _ = card_token;

    // Simulate different scenarios based on amount
    if (amount_cents < 0) return -1; // error
    if (amount_cents > 1000000) return 0; // decline large amounts
    return 1; // approve
}

/// Simulates calling a fraud detection service
/// Returns: 1 = safe, 0 = suspicious, -1 = definitely fraud
export fn check_fraud_score(user_id: u32, amount_cents: i32) i32 {
    // In production, this would call a fraud detection API
    _ = user_id;

    // Simulate: flag very large transactions as suspicious
    if (amount_cents > 500000) return -1;
    if (amount_cents > 100000) return 0;
    return 1;
}

/// Simulates checking inventory availability
/// Returns: available quantity (0 if not available)
export fn check_inventory(product_id: u32, quantity: u32) u32 {
    // In production, this would query a database/service
    _ = product_id;

    // Simulate: always have 10 in stock
    if (quantity <= 10) return quantity;
    return 10;
}

/// Simulates sending a notification
/// Returns: 1 = sent, 0 = failed
export fn send_notification(user_id: u32, message_type: i32) i32 {
    // In production, this would send email/SMS/push
    _ = user_id;
    _ = message_type;
    return 1;
}

/// Simulates an external API call that might be slow or fail
/// Returns: response code (positive = success, negative = error)
export fn call_external_api(endpoint_id: i32, payload_size: i32) i32 {
    _ = payload_size;
    // Simulate: endpoint 0 always succeeds, others may fail
    if (endpoint_id == 0) return 200;
    if (endpoint_id < 0) return -1;
    return 200;
}

// =============================================================================
// Pure Business Logic (no external calls - don't need mocking)
// =============================================================================

/// Calculate total with tax
export fn calculate_total(subtotal_cents: i32, tax_rate_bps: i32) i32 {
    // tax_rate_bps is in basis points (100 = 1%)
    const tax = @divTrunc(subtotal_cents * tax_rate_bps, 10000);
    return subtotal_cents + tax;
}

/// Apply discount code
/// Returns discounted amount or original if invalid code
export fn apply_discount(amount_cents: i32, discount_percent: i32) i32 {
    if (discount_percent <= 0 or discount_percent > 100) {
        return amount_cents;
    }
    const discount = @divTrunc(amount_cents * discount_percent, 100);
    return amount_cents - discount;
}

/// Validate payment amount
export fn validate_amount(amount_cents: i32) bool {
    return amount_cents > 0 and amount_cents <= 10000000; // max $100,000
}

/// Calculate shipping cost based on weight
export fn calculate_shipping(weight_grams: i32, distance_km: i32) i32 {
    if (weight_grams <= 0 or distance_km <= 0) return 0;

    // Base rate + weight factor + distance factor
    const base = 500; // $5.00 base
    const weight_cost = @divTrunc(weight_grams * 10, 1000); // $0.01 per gram
    const distance_cost = @divTrunc(distance_km * 5, 100); // $0.05 per km

    return base + weight_cost + distance_cost;
}

/// Check if amount qualifies for free shipping
export fn qualifies_for_free_shipping(amount_cents: i32) bool {
    return amount_cents >= 5000; // Free shipping over $50
}
