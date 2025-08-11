#!/usr/bin/env python3
"""
Standalone test for helper functions without Django dependencies
"""


def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values"""
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 1)


def test_helper_functions():
    """Test helper functions with mock data"""
    print("Testing helper functions...")

    try:
        # Test percentage change calculation
        result1 = calculate_percentage_change(100, 80)
        expected1 = 25.0
        assert result1 == expected1, f"Expected {expected1}, got {result1}"

        result2 = calculate_percentage_change(80, 100)
        expected2 = -20.0
        assert result2 == expected2, f"Expected {expected2}, got {result2}"

        result3 = calculate_percentage_change(50, 0)
        expected3 = 100
        assert result3 == expected3, f"Expected {expected3}, got {result3}"

        result4 = calculate_percentage_change(0, 50)
        expected4 = -100.0
        assert result4 == expected4, f"Expected {expected4}, got {result4}"

        result5 = calculate_percentage_change(0, 0)
        expected5 = 0
        assert result5 == expected5, f"Expected {expected5}, got {result5}"

        print("✅ calculate_percentage_change working correctly")

        # Test edge cases
        result6 = calculate_percentage_change(150, 100)
        expected6 = 50.0
        assert result6 == expected6, f"Expected {expected6}, got {result6}"

        result7 = calculate_percentage_change(75, 100)
        expected7 = -25.0
        assert result7 == expected7, f"Expected {expected7}, got {result7}"

        print("✅ Edge cases handled correctly")
        return True

    except AssertionError as e:
        print(f"❌ Assertion error: {e}")
        return False
    except Exception as e:
        print(f"❌ Helper function test error: {e}")
        return False


if __name__ == "__main__":
    success = test_helper_functions()
    if success:
        print("🎉 Helper functions validation passed!")
    else:
        print("❌ Helper functions validation failed!")
