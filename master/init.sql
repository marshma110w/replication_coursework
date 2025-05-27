-- Item_categories
CREATE TABLE item_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

-- Warehouses
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    contact_phone VARCHAR(20),
    working_hours JSONB,
    capacity INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

-- Items
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    barcode VARCHAR(100) UNIQUE,
    category_id INTEGER REFERENCES Item_categories(id),
    weight DECIMAL(10, 2),
    warehouse_id INTEGER REFERENCES Warehouses(id)
);

-- Employees
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    position VARCHAR(100),
    warehouse_id INTEGER REFERENCES Warehouses(id)
);

-- Создаем пользователя для репликации
CREATE USER repl_user WITH REPLICATION LOGIN PASSWORD 'repl_password';
CREATE PUBLICATION my_publication FOR ALL TABLES;

GRANT USAGE ON SCHEMA public TO repl_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO repl_user;