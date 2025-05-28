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
    quantity INTEGER NOT NULL DEFAULT 1,
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

CREATE TYPE shipment_status AS ENUM ('PENDING', 'PREPARED', 'COMPLETED');

-- Основная таблица выдачи
CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    courier_id INTEGER REFERENCES employees(id), -- теперь может быть NULL
    status shipment_status NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Таблица состава выдачи (товары и их количество)
CREATE TABLE shipment_items (
    shipment_id INTEGER NOT NULL REFERENCES shipments(id),
    item_id INTEGER NOT NULL REFERENCES items(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (shipment_id, item_id)
);

CREATE INDEX idx_shipments_status ON shipments(status);
CREATE INDEX idx_shipments_warehouse ON shipments(warehouse_id);
CREATE INDEX idx_shipments_courier ON shipments(courier_id);

-- Создаем пользователя для репликации
CREATE USER repl_user WITH REPLICATION LOGIN PASSWORD 'repl_password';
CREATE PUBLICATION my_publication FOR ALL TABLES;

GRANT USAGE ON SCHEMA public TO repl_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO repl_user;