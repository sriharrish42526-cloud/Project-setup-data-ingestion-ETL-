-- 1. Top 5 Funds by Total Asset Value Allocation (AUM)
SELECT f.scheme_name, p.aum 
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum DESC LIMIT 5;

-- 2. Average Asset NAV Per Calendar Month Context
SELECT amfi_code, strftime('%Y-%m', date) AS transaction_month, AVG(nav) AS avg_nav
FROM fact_nav
GROUP BY amfi_code, transaction_month;

-- 3. SIP Year-over-Year Transaction Volume Growth
SELECT strftime('%Y', transaction_date) AS year_axis, SUM(amount) AS total_sip_volume
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY year_axis;

-- 4. Geographic Penetration: Absolute Transactions Executed Grouped By State
SELECT state, COUNT(transaction_id) AS total_transactions, SUM(amount) AS gross_state_inflow
FROM fact_transactions
GROUP BY state
ORDER BY gross_state_inflow DESC;

-- 5. Institutional Fee Pruning: Low Expense Schemes (< 1%)
SELECT f.scheme_name, p.expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 0.01
ORDER BY p.expense_ratio ASC;

-- 6. Total Capital Redemption vs Subscription Balance Matrix
SELECT transaction_type, SUM(amount) AS nominal_aggregate_volume
FROM fact_transactions
GROUP BY transaction_type;

-- 7. Audit Compliance Layer: Non-Verified KYC Capital Inflows
SELECT kyc_status, COUNT(*) AS txn_count, SUM(amount) AS unverified_exposure_pool
FROM fact_transactions
WHERE kyc_status != 'Verified'
GROUP BY kyc_status;

-- 8. Scheme Return Performance Leaderboard Mapping
SELECT f.scheme_name, p.returns_1y, p.anomaly_flag
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.returns_1y DESC;

-- 9. Maximum Drawdown & Dynamic Variance Spread of Fund Net Asset Values
SELECT amfi_code, MAX(nav) AS peak_nav, MIN(nav) AS floor_nav, (MAX(nav) - MIN(nav)) AS systematic_spread
FROM fact_nav
GROUP BY amfi_code;

-- 10. High-Value Account Transactions Exceeding Layer Averages
SELECT transaction_id, amfi_code, amount, state
FROM fact_transactions
WHERE amount > (SELECT AVG(amount) FROM fact_transactions)
ORDER BY amount DESC LIMIT 10;

