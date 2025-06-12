from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from polars.plugins import register_plugin_function

from polars_fin._internal import __version__ as __version__

if TYPE_CHECKING:
    from polars_fin.typing import IntoExprColumn

LIB = Path(__file__).parent


def cap_gains(
    ttype: IntoExprColumn, qty: IntoExprColumn, amt: IntoExprColumn
) -> pl.Expr:
    """Calculate capital gains for a given transaction type, quantity, and amount.
    The function implements recursive logic to calculate capital gains using the **average cost method**.

    Args:
        ttype: Transaction type, e.g. "buy" or "sell". "buy" is keyword required for triggering the
            buying logic while "sell" is keyword required for triggering the selling logic. Any other
            value (ex. dividend, split, etc.) will be ignored.
        qty: Quantity of the transaction
        amt: Total amount of the transaction

    Returns:
        Polars Struct with the following fields:
        - "cumul_qty": Cumulative quantity for the specific security
        - "cumul_avg_cost": Cumulative average cost of the security
        - "avg_unit_cost": Average unit cost of the security
        - "cost_units_sold": Cost units sold
        - "realized_gain": Realized gain for the transaction

    Use `unnest()` to flatten the struct into separate columns.

    Example:
        >>> import polars as pl
        >>> from datetime import date
        >>> import polars_fin as pf
        >>> data = {
        ...     "date": [
        ...         date(2023, 1, 10),
        ...         date(2023, 2, 15),
        ...         date(2023, 3, 20),
        ...         date(2023, 4, 5),
        ...         date(2023, 5, 5),
        ...         date(2023, 6, 1),
        ...     ],
        ...     "security": ["XYZ", "XYZ", "XYZ", "XYZ", "XYZ", "XYZ"],
        ...     "type": ["buy", "buy", "sell", "dividend", "sell", "buy"],
        ...     "quantity": [100, 50, 30, 0, 120, 100],
        ...     "transaction_value": [1000.0, 600.0, 450.0, 12, 960, 700.0],
        ... }
        >>> df = pl.DataFrame(data)
        >>> result = df.with_columns(
        ...     pf.cap_gains("type", "quantity", "transaction_value").alias("cap_gains")
        ... ).select("cap_gains").unnest("cap_gains")
        >>> result
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
    """
    qty = pl.col(qty).cast(pl.Float64)
    ttype = pl.col(ttype).str.to_lowercase()
    return register_plugin_function(
        args=[ttype, qty, amt],
        plugin_path=LIB,
        function_name="cap_gains",
        is_elementwise=False,
    )
