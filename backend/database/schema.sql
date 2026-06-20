-- AgriDemand Pro - MySQL Schema
-- Run this first before starting the app

CREATE DATABASE IF NOT EXISTS agridemand;
USE agridemand;

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,         -- vegetable / fruit
    unit VARCHAR(20) DEFAULT 'Quintal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Markets table (TN mandis)
CREATE TABLE IF NOT EXISTS markets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(50) DEFAULT 'Tamil Nadu'
);

-- Price history table (from Kaggle + Agmarknet)
CREATE TABLE IF NOT EXISTS price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    market_id INT NOT NULL,
    price_date DATE NOT NULL,
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    modal_price DECIMAL(10,2),             -- most common price
    source VARCHAR(20) DEFAULT 'kaggle',   -- kaggle / agmarknet
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (market_id) REFERENCES markets(id),
    UNIQUE KEY unique_price (product_id, market_id, price_date)
);

-- Forecasts table (saved predictions)
CREATE TABLE IF NOT EXISTS forecasts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    market_id INT NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_price DECIMAL(10,2),
    predicted_demand VARCHAR(20),          -- HIGH / MEDIUM / LOW
    lower_bound DECIMAL(10,2),
    upper_bound DECIMAL(10,2),
    model_used VARCHAR(30) DEFAULT 'prophet',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (market_id) REFERENCES markets(id)
);

-- Wastage alerts table
CREATE TABLE IF NOT EXISTS wastage_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    market_id INT NOT NULL,
    alert_date DATE NOT NULL,
    risk_level VARCHAR(20),                -- HIGH / MEDIUM / LOW
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (market_id) REFERENCES markets(id)
);

-- Seed: Products
INSERT IGNORE INTO products (name, category) VALUES
('Tomato', 'vegetable'),
('Onion', 'vegetable'),
('Potato', 'vegetable'),
('Brinjal', 'vegetable'),
('Carrot', 'vegetable'),
('Cabbage', 'vegetable'),
('Cauliflower', 'vegetable'),
('Beans', 'vegetable'),
('Banana', 'fruit'),
('Mango', 'fruit'),
('Grapes', 'fruit'),
('Watermelon', 'fruit');

-- Seed: Markets (TN)
INSERT IGNORE INTO markets (name, district) VALUES
('Koyambedu', 'Chennai'),
('Erode', 'Erode'),
('Coimbatore', 'Coimbatore'),
('Madurai', 'Madurai'),
('Salem', 'Salem'),
('Trichy', 'Tiruchirappalli'),
('Tirunelveli', 'Tirunelveli'),
('Vellore', 'Vellore');
