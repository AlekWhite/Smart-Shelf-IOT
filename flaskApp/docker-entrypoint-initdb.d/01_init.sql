-- users table for auth
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- items table
CREATE TABLE IF NOT EXISTS item (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    per_unit_weight FLOAT NOT NULL,
    image_link VARCHAR(500)
);

-- shelf table
CREATE TABLE IF NOT EXISTS shelf (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- junction table for shelf-item 
CREATE TABLE IF NOT EXISTS shelf_item (
    id SERIAL PRIMARY KEY,
    shelf_id INTEGER NOT NULL REFERENCES shelf(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL REFERENCES item(name) ON DELETE CASCADE,
    count INTEGER NOT NULL DEFAULT 0,
    restock_count INTEGER DEFAULT 0,
    allowed BOOLEAN DEFAULT FALSE NOT NULL,
    UNIQUE(shelf_id, item_name)
);

-- table for raw data
CREATE TABLE IF NOT EXISTS live_data (
    id SERIAL PRIMARY KEY,
    data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- function to delete old live_data records
CREATE OR REPLACE FUNCTION delete_old_live_data()
RETURNS trigger AS $$
BEGIN
    DELETE FROM live_data WHERE timestamp < NOW() - INTERVAL '10 seconds';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- trigger delete after each insert
CREATE TRIGGER trigger_delete_old_live_data
    AFTER INSERT ON live_data
    FOR EACH STATEMENT
    EXECUTE FUNCTION delete_old_live_data();


CREATE INDEX idx_item_name ON item(name);
CREATE INDEX idx_live_data_timestamp ON live_data(timestamp);
CREATE INDEX idx_shelf_item_shelf ON shelf_item(shelf_id);
CREATE INDEX idx_shelf_item_name ON shelf_item(item_name);