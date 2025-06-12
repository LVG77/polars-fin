import random
import time
from datetime import date, timedelta
from functools import partial

import polars as pl

import polars_fin as pf


# Create large df
def generate_large_df(
    n_rows: int = 1000000, securities: list[str] = ["XYZ"], seed: int = 42
) -> pl.DataFrame:
    security_quantities = {sec: 0 for sec in securities}

    data = {
        "date": [],
        "security": [],
        "type": [],
        "quantity": [],
        "price": [],
        "transaction_value": [],
    }
    random.seed(seed)
    start_date = date(2020, 1, 1)
    for i in range(n_rows):
        security = random.choice(securities)
        days_offset = random.randint(0, 1460)  # 4 years in days
        transaction_date = start_date + timedelta(days=days_offset)
        price = random.uniform(5.0, 500.0)
        current_qty = security_quantities[security]
        if current_qty == 0:
            transaction_type = "buy"
        elif current_qty < 10:
            transaction_type = random.choices(["buy", "dividend"], weights=[0.8, 0.2])[
                0
            ]
        else:
            transaction_type = random.choices(
                ["buy", "sell", "dividend"], weights=[0.4, 0.4, 0.2]
            )[0]

        if transaction_type == "buy":
            quantity = random.randint(5, 100)
            security_quantities[security] += quantity
            transaction_value = quantity * price
        elif transaction_type == "sell":
            quantity = min(current_qty, random.randint(1, 50))
            security_quantities[security] -= quantity
            transaction_value = quantity * price
        else:  # dividend
            quantity = 0
            transaction_value = quantity * random.uniform(0.10, 2)  # dividend per share

        data["date"].append(transaction_date)
        data["security"].append(security)
        data["type"].append(transaction_type)
        data["quantity"].append(quantity)
        data["price"].append(round(price, 2))
        data["transaction_value"].append(round(transaction_value, 2))

    print(f"Generated {len(data['date'])} transactions")
    print(f"Final security quantities: {security_quantities}")

    return pl.DataFrame(data)


large_df = generate_large_df(1_000_000, securities=["XYZ", "ABC", "DEF", "GHI", "JKL"])


def avg_cost_native(
    df: pl.DataFrame, type_col: str, qty_col: str, amount_col: str
) -> pl.DataFrame:
    "Assums that data is sorted by date"
    total_cost = 0.0
    unit_cost = 0.0
    total_qty = 0
    out = []
    for row in df.iter_rows(named=True):
        cap_gains = 0.0
        cus = 0.0  # cost of units sold
        typ = row[type_col]  # type of transaction (ex. 'buy', 'sell', 'div', etc.)
        q = row[qty_col]  # quantity
        amt = row[amount_col] or 0.0  # total transaction amount
        # update running cost & qty
        if typ == "buy":
            total_cost += amt
            total_qty += q
        elif typ == "sell":
            cus = unit_cost * q
            total_cost -= cus
            total_qty -= q
            cap_gains = amt - cus
        unit_cost = (total_cost / total_qty) if total_qty > 0 else 0.0
        out.append(
            {
                **row,
                "cumul_qty": total_qty,
                "cumul_avg_cost": total_cost,
                "avg_unit_cost": unit_cost,
                "cost_units_sold": cus,
                "realized_gain": cap_gains,
            }
        )
    return pl.DataFrame(out)


def calc_avg_cost_native(df: pl.DataFrame) -> pl.DataFrame:
    tic = time.perf_counter()
    avg_cost_native_gr = partial(
        avg_cost_native,
        type_col="type",
        qty_col="quantity",
        amount_col="transaction_value",
    )
    res = df.sort("date").group_by("security").map_groups(avg_cost_native_gr)
    toc = time.perf_counter()
    print(f"NATIVE: Time taken: {toc - tic:.4f} seconds")
    return res


def calc_avg_cost_rust(df: pl.DataFrame) -> pl.DataFrame:
    tic = time.perf_counter()
    res = (
        df.sort("date")
        # .group_by("security")
        # .agg(pf.cap_gains("type", "quantity", "transaction_value").alias("cap_gains"))
        .with_columns(
            pf.cap_gains("type", "quantity", "transaction_value")
            .over("security")
            .alias("cap_gains")
        )
    )
    toc = time.perf_counter()
    print(f"RUST: Time taken: {toc - tic:.4f} seconds")
    return res


naive_res = calc_avg_cost_native(large_df)
rust_res = calc_avg_cost_rust(large_df)
print(naive_res)
print(rust_res)
