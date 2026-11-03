\! chcp 65001

SET client_encoding TO 'UTF8';

-- 1. ОЧИЩАЕМ ВСЁ ---------------------------------------------------

TRUNCATE TABLE order_items RESTART IDENTITY CASCADE;
TRUNCATE TABLE orders       RESTART IDENTITY CASCADE;
TRUNCATE TABLE product      RESTART IDENTITY CASCADE;
TRUNCATE TABLE users        RESTART IDENTITY CASCADE;
TRUNCATE TABLE pvz          RESTART IDENTITY CASCADE;

-- 2. ВРЕМЕННЫЕ ТАБЛИЦЫ ----------------------------------------------

DROP TABLE IF EXISTS users_raw;
DROP TABLE IF EXISTS pvz_raw;
DROP TABLE IF EXISTS orders_raw;

CREATE TEMP TABLE users_raw (
    role_ru  text,
    fio      text,
    login    text,
    password text
);

CREATE TEMP TABLE pvz_raw (
    line text
);

CREATE TEMP TABLE orders_raw (
    order_no      text,
    article       text,
    order_date    text,
    delivery_date text,
    pvz_num       text,
    client_fio    text,
    pickup_code   text,
    status        text
);

-- 3. USERS ----------------------------------------------------------

\copy users_raw(role_ru, fio, login, password) FROM 'C:/Users/sxnfl/PycharmProjects/PythonProject/tables/user_import.csv' WITH (FORMAT csv, DELIMITER ';', HEADER true);

INSERT INTO users (fio, login, password, role)
SELECT
    fio,
    login,
    password,
    CASE role_ru
        WHEN 'Администратор'           THEN 'admin'
        WHEN 'Менеджер'                THEN 'manager'
        WHEN 'Авторизированный клиент' THEN 'client'
        ELSE 'client'
    END
FROM users_raw;

DROP TABLE users_raw;

-- 4. PRODUCT --------------------------------------------------------

\copy product(article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) FROM 'C:/Users/sxnfl/PycharmProjects/PythonProject/tables/Tovar.csv' WITH (FORMAT csv, DELIMITER ';', HEADER true, NULL '');

UPDATE product
SET photo = 'pics/' || photo
WHERE photo IS NOT NULL AND photo <> '';

-- 5. PVZ ------------------------------------------------------------

\copy pvz_raw(line) FROM 'C:/Users/sxnfl/PycharmProjects/PythonProject/tables/pvz_import.csv' WITH (FORMAT csv, DELIMITER E'\t', HEADER false);

INSERT INTO pvz (id_pvz, address)
SELECT
    row_number() OVER (ORDER BY (SELECT 1)) AS id_pvz,   -- ID: 1,2,3...
    trim(line)                               AS address  -- ВЕСЬ адрес с индексом
FROM pvz_raw;

DROP TABLE pvz_raw;

-- 6. ORDERS ---------------------------------------------------------

\copy orders_raw(order_no, article, order_date, delivery_date, pvz_num, client_fio, pickup_code, status) FROM 'C:/Users/sxnfl/PycharmProjects/PythonProject/tables/zakaz_import.csv' WITH (FORMAT csv, DELIMITER ';', HEADER true);

INSERT INTO orders (
    id_order,
    article,
    order_date,
    delivery_date,
    id_pvz,
    client_fio,
    pickup_code,
    status
)
SELECT
    order_no::integer,
    article,
    CASE
        WHEN order_date = '30.02.2025' THEN DATE '2025-02-28'
        ELSE TO_DATE(order_date, 'DD.MM.YYYY')
    END,
    TO_DATE(delivery_date, 'DD.MM.YYYY'),
    pvz_num::integer,            -- совпадает с id_pvz = 1..N
    client_fio,
    pickup_code::smallint,
    status
FROM orders_raw;

-- 7. ORDER_ITEMS ----------------------------------------------------

INSERT INTO order_items (id_order, id_product, amount)
SELECT
    r.order_no::integer          AS id_order,
    p.id_product                 AS id_product,
    (m[2])::smallint             AS amount
FROM orders_raw r
CROSS JOIN LATERAL regexp_matches(
    r.article,
    '([^,]+)\s*,\s*([0-9]+)',
    'g'
) AS m
JOIN product p
    ON p.article = trim(m[1]);

DROP TABLE orders_raw;

-- 8. SEQUENCES ------------------------------------------------------

SELECT setval('users_id_user_seq',      (SELECT COALESCE(max(id_user), 1) FROM users));
SELECT setval('product_id_product_seq', (SELECT COALESCE(max(id_product), 1) FROM product));
SELECT setval('orders_id_order_seq',    (SELECT COALESCE(max(id_order), 1) FROM orders));
