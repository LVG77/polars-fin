import polars as pl
from datetime import date
from polars.testing import assert_frame_equal

import polars_fin as pf


def test_cap_gains_single_security():
    """Test cap_gains with example from run.py"""
    # Example data from run.py
    data = {
        "date": [
            date(2023, 1, 10),
            date(2023, 2, 15),
            date(2023, 3, 20),
            date(2023, 4, 5),
            date(2023, 5, 5),
            date(2023, 6, 1),
        ],
        "security": ["XYZ", "XYZ", "XYZ", "XYZ", "XYZ", "XYZ"],
        "type": ["buy", "buy", "sell", "dividend", "sell", "buy"],
        "quantity": [100, 50, 30, 0, 120, 100],
        "price": [10.0, 12.0, 15.0, 0.1, 8.0, 7.0],
        "transaction_value": [1000.0, 600.0, 450.0, 12, 960, 700.0],
    }
    df = pl.DataFrame(data)
    
    result = df.with_columns(
        pf.cap_gains("type", "quantity", "transaction_value").alias("cap_gains")
    ).select("cap_gains").unnest("cap_gains")
    
    expected = pl.DataFrame({
        "cumul_qty": [100.0, 150.0, 120.0, 120.0, 0.0, 100.0],
        "cumul_avg_cost": [1000.0, 1600.0, 1280.0, 1280.0, 0.0, 700.0],
        "avg_unit_cost": [10.0, 10.666667, 10.666667, 10.666667, 0.0, 7.0],
        "cost_units_sold": [0.0, 0.0, 320.0, 0.0, 1280.0, 0.0],
        "realized_gain": [0.0, 0.0, 130.0, 0.0, -320.0, 0.0],
    })
    
    assert_frame_equal(result, expected)


def test_cap_gains_two_securities():
    """Test cap_gains with two securities using over('security')"""
    data = {
        "date": [
            date(2023, 1, 10),
            date(2023, 1, 15),
            date(2023, 2, 10),
            date(2023, 2, 15),
            date(2023, 3, 10),
            date(2023, 3, 15),
        ],
        "security": ["XYZ", "ABC", "XYZ", "ABC", "XYZ", "ABC"],
        "type": ["buy", "buy", "buy", "sell", "sell", "buy"],
        "quantity": [100, 50, 50, 25, 75, 30],
        "price": [10.0, 20.0, 12.0, 25.0, 15.0, 18.0],
        "transaction_value": [1000.0, 1000.0, 600.0, 625.0, 1125.0, 540.0],
    }
    df = pl.DataFrame(data)
    
    result = df.with_columns(
        pf.cap_gains("type", "quantity", "transaction_value").over("security").alias("cap_gains")
    )
    
    # Expected: XYZ should have separate calculations from ABC
    # XYZ: buy 100@10, buy 50@12, sell 75@15 -> realized gain of 187.5
    # ABC: buy 50@20, sell 25@25, buy 30@18 -> realized gain of 125
    
    xyz_gains = result.filter(pl.col("security") == "XYZ").select("cap_gains").unnest("cap_gains")
    abc_gains = result.filter(pl.col("security") == "ABC").select("cap_gains").unnest("cap_gains")
    
    expected_xyz = pl.DataFrame({
        "cumul_qty": [100.0, 150.0, 75.0],
        "cumul_avg_cost": [1000.0, 1600.0, 800.0],
        "avg_unit_cost": [10.0, 10.666667, 10.666667],
        "cost_units_sold": [0.0, 0.0, 800.0],
        "realized_gain": [0.0, 0.0, 325.0],
    })
    
    expected_abc = pl.DataFrame({
        "cumul_qty": [50.0, 25.0, 55.0],
        "cumul_avg_cost": [1000.0, 500.0, 1040.0],
        "avg_unit_cost": [20.0, 20.0, 18.909091],
        "cost_units_sold": [0.0, 500.0, 0.0],
        "realized_gain": [0.0, 125.0, 0.0],
    })
    
    assert_frame_equal(xyz_gains, expected_xyz)
    assert_frame_equal(abc_gains, expected_abc)

