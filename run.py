from datetime import date

import polars as pl

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
    "price": [10.0, 12.0, 15.0, 0.1, 8.0, 7.0],
    "transaction_value": [1000.0, 600.0, 450.0, 12, 960, 700.0],
}
cg = pl.DataFrame(data)
result = cg.with_columns(
    pf.cap_gains("type", "quantity", "transaction_value").alias("cap_gains")
)
print(result.select("cap_gains").unnest("cap_gains"))
