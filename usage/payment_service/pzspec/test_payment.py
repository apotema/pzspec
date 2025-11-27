"""
Test suite for Payment Service demonstrating PZSpec Mocking.

This example shows how to use mock_zig_function() to test business logic
by mocking external service calls at the FFI layer.

IMPORTANT: Mocking works at the Python/FFI boundary. When Python calls
a Zig function through get_function(), the mock intercepts it. Internal
Zig-to-Zig calls cannot be mocked.

Best practice: Design your system so that external service calls are
made from Python, allowing you to mock them during tests.
"""

import sys
from pathlib import Path

# Add the parent PZSpec to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from the framework package
from pzspec.zig_ffi import ZigLibrary
from pzspec.dsl import describe, it, expect
from pzspec.mock import (
    mock_zig_function,
    assert_called,
    assert_called_once,
    get_call_count,
    get_calls,
)
import ctypes

# Load the Zig library (auto-builds if needed)
zig = ZigLibrary()


# =============================================================================
# Helper Functions - Direct Zig Calls
# =============================================================================
def call_payment_gateway(amount_cents: int, card_token: str) -> int:
    """Call payment gateway."""
    func = zig.get_function(
        "call_payment_gateway",
        [ctypes.c_int32, ctypes.c_char_p],
        ctypes.c_int32,
    )
    return func(amount_cents, card_token.encode("utf-8"))


def check_fraud_score(user_id: int, amount_cents: int) -> int:
    """Check fraud score."""
    func = zig.get_function(
        "check_fraud_score",
        [ctypes.c_uint32, ctypes.c_int32],
        ctypes.c_int32,
    )
    return func(user_id, amount_cents)


def check_inventory(product_id: int, quantity: int) -> int:
    """Check inventory availability."""
    func = zig.get_function(
        "check_inventory",
        [ctypes.c_uint32, ctypes.c_uint32],
        ctypes.c_uint32,
    )
    return func(product_id, quantity)


def send_notification(user_id: int, message_type: int) -> int:
    """Send notification."""
    func = zig.get_function(
        "send_notification",
        [ctypes.c_uint32, ctypes.c_int32],
        ctypes.c_int32,
    )
    return func(user_id, message_type)


def call_external_api(endpoint_id: int, payload_size: int) -> int:
    """Call external API."""
    func = zig.get_function(
        "call_external_api",
        [ctypes.c_int32, ctypes.c_int32],
        ctypes.c_int32,
    )
    return func(endpoint_id, payload_size)


def calculate_total(subtotal_cents: int, tax_rate_bps: int) -> int:
    """Calculate total with tax."""
    func = zig.get_function("calculate_total", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
    return func(subtotal_cents, tax_rate_bps)


def apply_discount(amount_cents: int, discount_percent: int) -> int:
    """Apply discount to amount."""
    func = zig.get_function("apply_discount", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
    return func(amount_cents, discount_percent)


# =============================================================================
# Python-side Business Logic (orchestrates Zig calls - mockable)
# =============================================================================
def process_payment(user_id: int, product_id: int, quantity: int, amount_cents: int, card_token: str) -> int:
    """
    Process a payment - Python orchestrates the external service calls.

    This design allows us to mock individual Zig functions since Python
    makes each call through get_function().

    Returns:
        0 = success
        -1 = gateway timeout
        -2 = gateway declined
        -3 = fraud detected
        -4 = insufficient inventory
        -5 = invalid amount
    """
    # Validate amount
    if amount_cents <= 0:
        return -5  # invalid amount

    # Check fraud
    fraud_result = check_fraud_score(user_id, amount_cents)
    if fraud_result == -1:
        return -3  # fraud detected

    # Check inventory
    available = check_inventory(product_id, quantity)
    if available < quantity:
        return -4  # insufficient inventory

    # Call payment gateway
    gateway_result = call_payment_gateway(amount_cents, card_token)
    if gateway_result == -1:
        return -1  # gateway timeout
    if gateway_result == 0:
        return -2  # gateway declined

    # Success - send notification
    send_notification(user_id, 1)
    return 0  # success


def process_payment_with_retry(
    user_id: int, product_id: int, quantity: int, amount_cents: int, card_token: str, max_retries: int
) -> int:
    """Process payment with retry logic on gateway timeout."""
    if amount_cents <= 0:
        return -5

    fraud_result = check_fraud_score(user_id, amount_cents)
    if fraud_result == -1:
        return -3

    available = check_inventory(product_id, quantity)
    if available < quantity:
        return -4

    # Try gateway with retries
    for _ in range(max_retries + 1):
        gateway_result = call_payment_gateway(amount_cents, card_token)
        if gateway_result == 1:
            send_notification(user_id, 1)
            return 0  # success
        if gateway_result == 0:
            return -2  # declined - don't retry
        # gateway_result == -1 means timeout, retry

    return -1  # exhausted retries


# =============================================================================
# Tests Without Mocking (pure business logic)
# =============================================================================

with describe("Payment Calculations (no mocking needed)"):

    @it("should calculate total with tax")
    def test_calculate_total():
        # 1000 cents ($10.00) with 8.25% tax (825 basis points)
        result = calculate_total(1000, 825)
        expect(result).to_equal(1082)

    @it("should apply percentage discount")
    def test_apply_discount():
        result = apply_discount(1000, 20)
        expect(result).to_equal(800)

    @it("should reject invalid discount")
    def test_invalid_discount():
        expect(apply_discount(1000, 0)).to_equal(1000)
        expect(apply_discount(1000, -10)).to_equal(1000)
        expect(apply_discount(1000, 150)).to_equal(1000)


# =============================================================================
# Tests With Mocking - Fixed Return Values
# =============================================================================

with describe("Payment Processing - Mocking External Services"):

    @it("should succeed when all services return success")
    def test_successful_payment():
        with mock_zig_function("check_fraud_score", returns=1):  # safe
            with mock_zig_function("check_inventory", returns=5):  # available
                with mock_zig_function("call_payment_gateway", returns=1):  # approved
                    with mock_zig_function("send_notification", returns=1):
                        result = process_payment(123, 456, 2, 5000, "tok_visa")
                        expect(result).to_equal(0)  # success

    @it("should fail when fraud is detected")
    def test_fraud_detected():
        with mock_zig_function("check_fraud_score", returns=-1):  # fraud
            result = process_payment(123, 456, 1, 5000, "tok_stolen")
            expect(result).to_equal(-3)  # fraud detected

    @it("should fail when inventory is insufficient")
    def test_insufficient_inventory():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=2):  # only 2 available
                result = process_payment(123, 456, 5, 5000, "tok_visa")
                expect(result).to_equal(-4)  # insufficient inventory

    @it("should fail when payment gateway times out")
    def test_gateway_timeout():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                with mock_zig_function("call_payment_gateway", returns=-1):  # timeout
                    result = process_payment(123, 456, 1, 5000, "tok_visa")
                    expect(result).to_equal(-1)  # gateway timeout

    @it("should fail when payment is declined")
    def test_gateway_declined():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                with mock_zig_function("call_payment_gateway", returns=0):  # declined
                    result = process_payment(123, 456, 1, 5000, "tok_declined")
                    expect(result).to_equal(-2)  # gateway declined


# =============================================================================
# Tests With Mocking - Sequential Return Values (Retry Logic)
# =============================================================================

with describe("Payment Retry Logic - Sequential Mocking"):

    @it("should succeed after retrying on timeout")
    def test_retry_success():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                # First two calls timeout, third succeeds
                with mock_zig_function("call_payment_gateway", returns_sequence=[-1, -1, 1]):
                    with mock_zig_function("send_notification", returns=1):
                        result = process_payment_with_retry(123, 456, 1, 5000, "tok_visa", 3)
                        expect(result).to_equal(0)  # success

    @it("should fail after exhausting all retries")
    def test_retry_exhausted():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                # All calls timeout
                with mock_zig_function("call_payment_gateway", returns_sequence=[-1, -1, -1, -1]) as mock:
                    result = process_payment_with_retry(123, 456, 1, 5000, "tok_visa", 2)
                    expect(result).to_equal(-1)  # timeout
                    expect(mock.call_count).to_equal(3)  # initial + 2 retries

    @it("should not retry on decline")
    def test_no_retry_on_decline():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                with mock_zig_function("call_payment_gateway", returns_sequence=[0, 1, 1]) as mock:
                    result = process_payment_with_retry(123, 456, 1, 5000, "tok_declined", 3)
                    expect(result).to_equal(-2)  # declined
                    expect(mock.call_count).to_equal(1)  # only one attempt


# =============================================================================
# Tests With Mocking - Side Effects (Custom Logic)
# =============================================================================

with describe("Payment Processing - Side Effect Mocking"):

    @it("should use custom side effect for fraud scoring")
    def test_fraud_side_effect():
        def custom_fraud_check(user_id, amount_cents):
            if user_id == 666:
                return -1  # fraud
            return 1  # safe

        with mock_zig_function("check_fraud_score", side_effect=custom_fraud_check):
            with mock_zig_function("check_inventory", returns=10):
                with mock_zig_function("call_payment_gateway", returns=1):
                    with mock_zig_function("send_notification", returns=1):
                        # Normal user succeeds
                        result1 = process_payment(123, 456, 1, 5000, "tok_visa")
                        expect(result1).to_equal(0)

                        # Suspicious user fails
                        result2 = process_payment(666, 456, 1, 5000, "tok_visa")
                        expect(result2).to_equal(-3)

    @it("should use side effect for dynamic gateway responses")
    def test_gateway_side_effect():
        call_count = [0]

        def flaky_gateway(amount, token):
            call_count[0] += 1
            # Fail first 2 calls, then succeed
            if call_count[0] <= 2:
                return -1
            return 1

        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                with mock_zig_function("call_payment_gateway", side_effect=flaky_gateway):
                    with mock_zig_function("send_notification", returns=1):
                        result = process_payment_with_retry(123, 456, 1, 5000, "tok_visa", 3)
                        expect(result).to_equal(0)
                        expect(call_count[0]).to_equal(3)


# =============================================================================
# Tests With Mocking - Call Tracking and Assertions
# =============================================================================

with describe("Mock Call Tracking"):

    @it("should track that notification was sent on success")
    def test_notification_sent():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                with mock_zig_function("call_payment_gateway", returns=1):
                    with mock_zig_function("send_notification", returns=1) as mock:
                        result = process_payment(123, 456, 1, 5000, "tok_visa")
                        expect(result).to_equal(0)
                        assert_called("send_notification")
                        assert_called_once("send_notification")
                        expect(mock.call_count).to_equal(1)

    @it("should not send notification on failure")
    def test_notification_not_sent_on_failure():
        with mock_zig_function("check_fraud_score", returns=-1):
            with mock_zig_function("send_notification", returns=1) as mock:
                result = process_payment(123, 456, 1, 5000, "tok_visa")
                expect(result).to_equal(-3)
                expect(mock.call_count).to_equal(0)

    @it("should track multiple gateway calls during retry")
    def test_track_retry_calls():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                with mock_zig_function("call_payment_gateway", returns_sequence=[-1, -1, 1]):
                    with mock_zig_function("send_notification", returns=1):
                        result = process_payment_with_retry(123, 456, 1, 5000, "tok_visa", 3)
                        expect(result).to_equal(0)
                        expect(get_call_count("call_payment_gateway")).to_equal(3)

    @it("should access call arguments")
    def test_call_arguments():
        with mock_zig_function("check_fraud_score", returns=1):
            with mock_zig_function("check_inventory", returns=10):
                with mock_zig_function("call_payment_gateway", returns=1):
                    with mock_zig_function("send_notification", returns=1):
                        process_payment(123, 456, 1, 9999, "tok_visa")

                        calls = get_calls("check_fraud_score")
                        expect(len(calls)).to_equal(1)
                        expect(calls[0].args[0]).to_equal(123)  # user_id
                        expect(calls[0].args[1]).to_equal(9999)  # amount


# =============================================================================
# Tests - Direct Function Mocking (simpler examples)
# =============================================================================

with describe("Direct Function Mocking"):

    @it("should mock function with fixed return value")
    def test_mock_fixed_return():
        # Mock returns a fixed value regardless of inputs
        with mock_zig_function("call_external_api", returns=500):
            result1 = call_external_api(0, 100)
            result2 = call_external_api(99, 999)
            expect(result1).to_equal(500)
            expect(result2).to_equal(500)

    @it("should mock with sequence for pagination")
    def test_mock_pagination():
        # Simulate paginated API responses
        with mock_zig_function("call_external_api", returns_sequence=[200, 200, 404]):
            expect(call_external_api(1, 0)).to_equal(200)  # page 1
            expect(call_external_api(2, 0)).to_equal(200)  # page 2
            expect(call_external_api(3, 0)).to_equal(404)  # no more pages

    @it("should restore original behavior after mock context exits")
    def test_mock_context_cleanup():
        # Inside mock context
        with mock_zig_function("check_fraud_score", returns=99):
            mocked = check_fraud_score(1, 1000)
            expect(mocked).to_equal(99)

        # Outside mock context - back to real implementation
        # Real implementation returns 1 for amounts <= 100000
        real = check_fraud_score(1, 1000)
        expect(real).to_equal(1)  # safe (real implementation)
