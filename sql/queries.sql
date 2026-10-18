-- Business question: Which facilities and medicines had the lowest stock coverage last month?
SELECT facility_id, medicine_id, closing_stock, days_of_stock
FROM inventory_summary
WHERE month = '2025-12'
ORDER BY days_of_stock ASC;

-- Business question: Which medicines had the most stock-out days across facilities?
SELECT medicine_id, SUM(stockout_days) AS total_stockout_days
FROM inventory_summary
GROUP BY medicine_id
ORDER BY total_stockout_days DESC;

-- Business question: Which orders were delayed beyond policy lead time?
SELECT facility_id, medicine_id, expected_delivery_date, actual_delivery_date
FROM deliveries
WHERE actual_delivery_date > expected_delivery_date;

-- Business question: Which facility-medicine combinations need immediate reorder action?
SELECT facility_id, medicine_id, stock_on_hand, reorder_point, reorder_quantity
FROM inventory_summary
WHERE stock_on_hand < reorder_point;
