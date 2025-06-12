#![allow(clippy::unused_unit)]
use polars::prelude::*;
use pyo3_polars::derive::polars_expr;


// Fn that returns output schema
fn avg_cost_output_schema(_input_fields: &[Field]) -> PolarsResult<Field> {
    let fields = vec![
        Field::new("cumul_qty".into(), DataType::Float64),
        Field::new("cumul_avg_cost".into(), DataType::Float64),
        Field::new("avg_unit_cost".into(), DataType::Float64),
        Field::new("cost_units_sold".into(), DataType::Float64),
        Field::new("realized_gain".into(), DataType::Float64),
    ];
    Ok(Field::new("avg_cost".into(), DataType::Struct(fields)))
}

// #[polars_expr(output_type=Float64)]
#[polars_expr(output_type_func=avg_cost_output_schema)]
fn cap_gains(inputs: &[Series]) -> PolarsResult<Series> {
    let type_col: &StringChunked = inputs[0].str()?;
    let qty_col: &Float64Chunked = inputs[1].f64()?;
    let amt_col: &Float64Chunked = inputs[2].f64()?;

    let mut total_qty: f64 = 0.0;
    let mut total_cost: f64 = 0.0;

    let mut cumul_qty_vec: Vec<f64> = Vec::with_capacity(type_col.len());
    let mut cumul_avg_cost_vec: Vec<f64> = Vec::with_capacity(type_col.len());
    let mut avg_unit_cost_vec: Vec<f64> = Vec::with_capacity(type_col.len());
    let mut cost_units_sold_vec: Vec<f64> = Vec::with_capacity(type_col.len());
    let mut realized_gain_vec: Vec<f64> = Vec::with_capacity(type_col.len());

    for ((typ, qty_opt), amt_opt) in type_col.into_iter().zip(qty_col.into_iter()).zip(amt_col.into_iter()) {
        let qty = qty_opt.unwrap_or(0.0);
        let amt = amt_opt.unwrap_or(0.0);
        // Calculate unit cost before the current transaction
        let unit_cost = if total_qty > 0.0 { total_cost / total_qty } else { 0.0 };
        let mut cost_units_sold = 0.0;
        let mut realized_gain = 0.0;
        if let Some(transaction_type) = typ {
            match transaction_type {
                "buy" => {
                    total_cost += amt;
                    total_qty += qty;
                }
                "sell" => {
                    cost_units_sold = unit_cost * qty;
                    total_cost -= cost_units_sold;
                    total_qty -= qty;
                    realized_gain = amt - cost_units_sold;
                },
                // For all other types (ex. divs, etc. do nothing to the cost basis)
                _ => {}
            }
        }
        // Calculate the new unit cost
        let new_unit_cost = if total_qty > 0.0 { total_cost / total_qty } else { 0.0 };

        cumul_qty_vec.push(total_qty);
        cumul_avg_cost_vec.push(total_cost);
        avg_unit_cost_vec.push(new_unit_cost);
        cost_units_sold_vec.push(cost_units_sold);
        realized_gain_vec.push(realized_gain);
    
    }
    let s_cumul_qty = Series::new("cumul_qty".into(), &cumul_qty_vec);
    let s_cumul_avg_cost = Series::new("cumul_avg_cost".into(), &cumul_avg_cost_vec);
    let s_avg_unit_cost = Series::new("avg_unit_cost".into(), &avg_unit_cost_vec);
    let s_cost_units_sold = Series::new("cost_units_sold".into(), &cost_units_sold_vec);
    let s_realized_gain = Series::new("realized_gain".into(), &realized_gain_vec);

    let fields = &vec![
        s_cumul_qty,
        s_cumul_avg_cost,
        s_avg_unit_cost,
        s_cost_units_sold,
        s_realized_gain,
    ];

    StructChunked::from_series("avg_cost".into(), fields[0].len(), fields.iter())
        .map(|ca| ca.into_series())
}
