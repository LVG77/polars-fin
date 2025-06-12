# polars-fin

A plugin for [polars](https://github.com/pola-rs/polars) to efficiently calculate financial metrics.

To install the plugin, run `pip install polars-fin`.

## Capital Gains Calculation

Currently, the only function in the plugin `cap_gains(...)` is for calculating capital gains based on the average cost basis of a security.

### Usage

The `cap_gains` function calculates capital gains using the **average cost method**. It takes three parameters:

- `ttype`: Transaction type ("buy" for buying logic, "sell" for selling logic, other values are ignored)
- `qty`: Quantity of the transaction 
- `amt`: Total amount of the transaction

Returns a Polars Struct with fields for cumulative quantity, average cost, unit cost, cost of units sold, and realized gain. Use `unnest()` to flatten into separate columns.

```python
import polars as pl
from datetime import date
import polars_fin as pf

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
    "transaction_value": [1000.0, 600.0, 450.0, 12, 960, 700.0],
}
df = pl.DataFrame(data)
result = df.with_columns(
    pf.cap_gains("type", "quantity", "transaction_value").alias("cap_gains")
).select("cap_gains").unnest("cap_gains")
result
```

Output:
```
shape: (6, 5)
┌───────────┬────────────────┬───────────────┬─────────────────┬───────────────┐
│ cumul_qty ┆ cumul_avg_cost ┆ avg_unit_cost ┆ cost_units_sold ┆ realized_gain │
│ ---       ┆ ---            ┆ ---           ┆ ---             ┆ ---           │
│ f64       ┆ f64            ┆ f64           ┆ f64             ┆ f64           │
╞═══════════╪════════════════╪═══════════════╪═════════════════╪═══════════════╡
│ 100.0     ┆ 1000.0         ┆ 10.0          ┆ 0.0             ┆ 0.0           │
│ 150.0     ┆ 1600.0         ┆ 10.666667     ┆ 0.0             ┆ 0.0           │
│ 120.0     ┆ 1280.0         ┆ 10.666667     ┆ 320.0           ┆ 130.0         │
│ 120.0     ┆ 1280.0         ┆ 10.666667     ┆ 0.0             ┆ 0.0           │
│ 0.0       ┆ 0.0            ┆ 0.0           ┆ 1280.0          ┆ -320.0        │
│ 100.0     ┆ 700.0          ┆ 7.0           ┆ 0.0             ┆ 0.0           │
└───────────┴────────────────┴───────────────┴─────────────────┴───────────────┘
```
