--
-- PostgreSQL database dump
--

\restrict qpeXAyLSswW2ib0PVZMPsMCoe5m4z7ClV6cgfO6EX2QrBxiwFjJh5foEVxdKhaj

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_items (
    id_order integer NOT NULL,
    id_product integer NOT NULL,
    amount smallint NOT NULL
);


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    id_order integer NOT NULL,
    article character varying(50) NOT NULL,
    order_date date NOT NULL,
    delivery_date date,
    id_pvz integer NOT NULL,
    client_fio text NOT NULL,
    pickup_code smallint NOT NULL,
    status text NOT NULL,
    CONSTRAINT chk_orders_dates CHECK (((delivery_date IS NULL) OR (delivery_date >= order_date)))
);


--
-- Name: orders_id_order_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.orders_id_order_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_id_order_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.orders_id_order_seq OWNED BY public.orders.id_order;


--
-- Name: product; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.product (
    id_product integer NOT NULL,
    article character varying(50) NOT NULL,
    name text NOT NULL,
    uom character varying(50),
    price numeric(10,2),
    supplier text,
    manufacturer text,
    category text,
    discount smallint DEFAULT 0,
    amount smallint DEFAULT 0,
    description text,
    photo text
);


--
-- Name: product_id_product_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.product_id_product_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: product_id_product_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.product_id_product_seq OWNED BY public.product.id_product;


--
-- Name: pvz; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pvz (
    id_pvz integer NOT NULL,
    address text NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id_user integer NOT NULL,
    fio text NOT NULL,
    login character varying(100) NOT NULL,
    password character varying(100) NOT NULL,
    role character varying(20) NOT NULL
);


--
-- Name: users_id_user_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_user_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_user_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_user_seq OWNED BY public.users.id_user;


--
-- Name: orders id_order; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders ALTER COLUMN id_order SET DEFAULT nextval('public.orders_id_order_seq'::regclass);


--
-- Name: product id_product; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product ALTER COLUMN id_product SET DEFAULT nextval('public.product_id_product_seq'::regclass);


--
-- Name: users id_user; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id_user SET DEFAULT nextval('public.users_id_user_seq'::regclass);


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.order_items (id_order, id_product, amount) VALUES (1, 1, 2);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (1, 2, 2);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (2, 3, 1);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (2, 4, 1);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (4, 7, 5);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (4, 8, 4);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (5, 1, 2);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (5, 2, 2);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (8, 7, 5);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (8, 8, 4);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (9, 9, 5);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (9, 10, 1);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (10, 11, 5);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (10, 12, 5);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (7, 5, 10);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (7, 6, 10);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (6, 3, 1);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (6, 4, 1);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (24, 1, 1);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (25, 1, 1);
INSERT INTO public.order_items (id_order, id_product, amount) VALUES (26, 1, 1);


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (1, 'А112Т4, 2, F635R4, 2', '2025-02-27', '2025-04-20', 1, 'Степанов Михаил Артёмович', 901, 'Завершен');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (2, 'H782T5, 1, G783F5, 1', '2022-09-28', '2025-04-21', 11, 'Никифорова Весения Николаевна', 902, 'Завершен');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (4, 'F572H7, 5, D329H3, 4', '2025-02-20', '2025-04-23', 11, 'Одинцов Серафим Артёмович', 904, 'Завершен');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (5, 'А112Т4, 2, F635R4, 2', '2025-03-17', '2025-04-24', 2, 'Степанов Михаил Артёмович', 905, 'Завершен');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (8, 'F572H7, 5, D329H3, 4', '2025-03-31', '2025-04-27', 19, 'Одинцов Серафим Артёмович', 908, 'Новый ');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (9, 'B320R5, 5, G432E4, 1', '2025-04-02', '2025-04-28', 5, 'Степанов Михаил Артёмович', 909, 'Новый ');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (10, 'S213E3, 5, E482R4, 5', '2025-04-03', '2025-04-29', 19, 'Степанов Михаил Артёмович', 910, 'Завершен');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (7, 'J384T6, 10, D572U8, 10', '2025-02-28', '2025-04-26', 32, 'Сазонов Руслан Германович', 907, 'Новый');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (6, 'H782T5, 1, G783F5, 1', '2025-03-01', '2025-04-25', 9, 'Никифорова Весения Николаевна', 906, 'Новый');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (24, 'А112Т4, 1', '2026-01-01', '2026-02-01', 1, 'Иванов Иван Иванович', 1234, 'Новый');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (25, 'А112Т4, 1', '2026-01-01', '2026-02-01', 1, 'Иванов Иван Иванович', 1234, 'Новый');
INSERT INTO public.orders (id_order, article, order_date, delivery_date, id_pvz, client_fio, pickup_code, status) VALUES (26, 'А112Т4, 1', '2026-02-04', '2026-02-14', 1, 'Иванов Александр Иванович', 123, 'Новый');


--
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (13, 'S634B5', 'Кеды', 'шт.', 5500.00, 'Обувь для вас', 'CROSBY', 'Мужская обувь', 3, 0, 'Кеды Caprice мужские демисезонные, размер 42, цвет черный', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (14, 'K345R4', 'Полуботинки', 'шт.', 2100.00, 'Обувь для вас', 'CROSBY', 'Мужская обувь', 2, 3, '407700/01-02 Полуботинки мужские CROSBY', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (15, 'O754F4', 'Туфли', 'шт.', 5400.00, 'Обувь для вас', 'Rieker', 'Женская обувь', 4, 18, 'Туфли женские демисезонные Rieker артикул 55073-68/37', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (16, 'G531F4', 'Ботинки', 'шт.', 6600.00, 'Kari', 'Kari', 'Женская обувь', 12, 9, 'Ботинки женские зимние ROMER арт. 893167-01 Черный', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (17, 'J542F5', 'Тапочки', 'шт.', 500.00, 'Kari', 'Kari', 'Мужская обувь', 13, 0, 'Тапочки мужские Арт.70701-55-67син р.41', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (18, 'B431R5', 'Ботинки', 'шт.', 2700.00, 'Обувь для вас', 'Rieker', 'Мужская обувь', 2, 5, 'Мужские кожаные ботинки/мужские ботинки', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (19, 'P764G4', 'Туфли', 'шт.', 6800.00, 'Kari', 'CROSBY', 'Женская обувь', 15, 15, 'Туфли женские, ARGO, размер 38', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (20, 'C436G5', 'Ботинки', 'шт.', 10200.00, 'Kari', 'Alessio Nesca', 'Женская обувь', 15, 9, 'Ботинки женские, ARGO, размер 40', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (21, 'F427R5', 'Ботинки', 'шт.', 11800.00, 'Обувь для вас', 'Rieker', 'Женская обувь', 15, 11, 'Ботинки на молнии с декоративной пряжкой FRAU', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (22, 'N457T5', 'Полуботинки', 'шт.', 4600.00, 'Kari', 'CROSBY', 'Женская обувь', 3, 13, 'Полуботинки Ботинки черные зимние, мех', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (23, 'D364R4', 'Туфли', 'шт.', 12400.00, 'Kari', 'Kari', 'Женская обувь', 16, 5, 'Туфли Luiza Belly женские Kate-lazo черные из натуральной замши', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (24, 'S326R5', 'Тапочки', 'шт.', 9900.00, 'Обувь для вас', 'CROSBY', 'Мужская обувь', 17, 15, 'Мужские кожаные тапочки "Профиль С.Дали" ', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (25, 'L754R4', 'Полуботинки', 'шт.', 1700.00, 'Kari', 'Kari', 'Женская обувь', 2, 7, 'Полуботинки kari женские WB2020SS-26, размер 38, цвет: черный', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (26, 'M542T5', 'Кроссовки', 'шт.', 2800.00, 'Обувь для вас', 'Rieker', 'Мужская обувь', 18, 3, 'Кроссовки мужские TOFA', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (27, 'D268G5', 'Туфли', 'шт.', 4399.00, 'Обувь для вас', 'Rieker', 'Женская обувь', 3, 12, 'Туфли Rieker женские демисезонные, размер 36, цвет коричневый', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (28, 'T324F5', 'Сапоги', 'шт.', 4699.00, 'Kari', 'CROSBY', 'Женская обувь', 2, 5, 'Сапоги замша Цвет: синий', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (29, 'K358H6', 'Тапочки', 'шт.', 599.00, 'Kari', 'Rieker', 'Мужская обувь', 20, 2, 'Тапочки мужские син р.41', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (7, 'F572H7', 'Туфли', 'шт.', 2700.00, 'Kari', 'Marco Tozzi', 'Женская обувь', 2, 14, 'Туфли Marco Tozzi женские летние, размер 39, цвет черный', 'pics/7.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (2, 'F635R4', 'Ботинки', 'шт.', 3244.00, 'Обувь для вас', 'Marco Tozzi', 'Женская обувь', 2, 13, 'Ботинки Marco Tozzi женские демисезонные, размер 39, цвет бежевый', 'pics/2.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (6, 'D572U8', 'Кроссовки', 'шт.', 4100.00, 'Обувь для вас', 'Рос', 'Мужская обувь', 3, 16, '129615-4 Кроссовки мужские', 'pics/6.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (1, 'А112Т4', 'Ботинки', 'шт.', 4990.00, 'Kari', 'Kari', 'Женская обувь', 3, 3, 'Женские Ботинки демисезонные kari', 'pics/1.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (3, 'H782T5', 'Туфли', 'шт.', 4499.00, 'Kari', 'Kari', 'Мужская обувь', 4, 5, 'Туфли kari мужские классика MYZ21AW-450A, размер 43, цвет: черный', 'pics/3.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (8, 'D329H3', 'Полуботинки', 'шт.', 1890.00, 'Обувь для вас', 'Alessio Nesca', 'Женская обувь', 4, 4, 'Полуботинки Alessio Nesca женские 3-30797-47, размер 37, цвет: бордовый', 'pics/8.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (9, 'B320R5', 'Туфли', 'шт.', 4300.00, 'Kari', 'Rieker', 'Женская обувь', 2, 6, 'Туфли Rieker женские демисезонные, размер 41, цвет коричневый', 'pics/9.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (11, 'S213E3', 'Полуботинки', 'шт.', 2156.00, 'Обувь для вас', 'CROSBY', 'Мужская обувь', 3, 6, '407700/01-01 Полуботинки мужские CROSBY', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (12, 'E482R4', 'Полуботинки', 'шт.', 1800.00, 'Kari', 'Kari', 'Женская обувь', 2, 14, 'Полуботинки kari женские MYZ20S-149, размер 41, цвет: черный', NULL);
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (4, 'G783F5', 'Ботинки', 'шт.', 5900.00, 'Kari', 'Рос', 'Мужская обувь', 2, 8, 'Мужские ботинки Рос-Обувь кожаные с натуральным мехом', 'pics/4.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (5, 'J384T6', 'Ботинки', 'шт.', 3800.00, 'Обувь для вас', 'Rieker', 'Мужская обувь', 2, 26, 'B3430/14 Полуботинки мужские Rieker', 'pics/5.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (10, 'G432E4', 'Туфли', 'шт.', 2800.00, 'Kari', 'Kari', 'Женская обувь', 3, 15, 'Туфли kari женские TR-YR-413017, размер 37, цвет: черный', 'pics/10.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (35, 'LB22222', 'Чук и Гек', 'пара', 29999.00, 'АСТ', 'ИП Гайдар', 'Кошачья обувь', 99, 1, 'Два сапога пара и оба левые.', 'pics/prod_0ebdd67efd234f179574b09a91af24a6.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (38, 'PPT12', 'Мык и Пык', 'sd', 9644.00, 'sfkdf', 'Stepan CO', 'Кошачья обувь', 27, 56, '12ajasj aafja', 'pics/prod_2f25e43fd52a476d987dc5fde912a2ba.jpg');
INSERT INTO public.product (id_product, article, name, uom, price, supplier, manufacturer, category, discount, amount, description, photo) VALUES (40, '123456A', 'Test', 'пара', 1000.00, 'Test', 'CROSBY', 'Женская обувь', 25, 2, 'Test', 'pics/prod_13643f92aefc4dc5b796d8ce5d7d1a5b.jpg');


--
-- Data for Name: pvz; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.pvz (id_pvz, address) VALUES (1, '420151, г. Лесной, ул. Вишневая, 32');
INSERT INTO public.pvz (id_pvz, address) VALUES (2, '125061, г. Лесной, ул. Подгорная, 8');
INSERT INTO public.pvz (id_pvz, address) VALUES (3, '630370, г. Лесной, ул. Шоссейная, 24');
INSERT INTO public.pvz (id_pvz, address) VALUES (4, '400562, г. Лесной, ул. Зеленая, 32');
INSERT INTO public.pvz (id_pvz, address) VALUES (5, '614510, г. Лесной, ул. Маяковского, 47');
INSERT INTO public.pvz (id_pvz, address) VALUES (6, '410542, г. Лесной, ул. Светлая, 46');
INSERT INTO public.pvz (id_pvz, address) VALUES (7, '620839, г. Лесной, ул. Цветочная, 8');
INSERT INTO public.pvz (id_pvz, address) VALUES (8, '443890, г. Лесной, ул. Коммунистическая, 1');
INSERT INTO public.pvz (id_pvz, address) VALUES (9, '603379, г. Лесной, ул. Спортивная, 46');
INSERT INTO public.pvz (id_pvz, address) VALUES (10, '603721, г. Лесной, ул. Гоголя, 41');
INSERT INTO public.pvz (id_pvz, address) VALUES (11, '410172, г. Лесной, ул. Северная, 13');
INSERT INTO public.pvz (id_pvz, address) VALUES (12, '614611, г. Лесной, ул. Молодежная, 50');
INSERT INTO public.pvz (id_pvz, address) VALUES (13, '454311, г.Лесной, ул. Новая, 19');
INSERT INTO public.pvz (id_pvz, address) VALUES (14, '660007, г.Лесной, ул. Октябрьская, 19');
INSERT INTO public.pvz (id_pvz, address) VALUES (15, '603036, г. Лесной, ул. Садовая, 4');
INSERT INTO public.pvz (id_pvz, address) VALUES (16, '394060, г.Лесной, ул. Фрунзе, 43');
INSERT INTO public.pvz (id_pvz, address) VALUES (17, '410661, г. Лесной, ул. Школьная, 50');
INSERT INTO public.pvz (id_pvz, address) VALUES (18, '625590, г. Лесной, ул. Коммунистическая, 20');
INSERT INTO public.pvz (id_pvz, address) VALUES (19, '625683, г. Лесной, ул. 8 Марта');
INSERT INTO public.pvz (id_pvz, address) VALUES (20, '450983, г.Лесной, ул. Комсомольская, 26');
INSERT INTO public.pvz (id_pvz, address) VALUES (21, '394782, г. Лесной, ул. Чехова, 3');
INSERT INTO public.pvz (id_pvz, address) VALUES (22, '603002, г. Лесной, ул. Дзержинского, 28');
INSERT INTO public.pvz (id_pvz, address) VALUES (23, '450558, г. Лесной, ул. Набережная, 30');
INSERT INTO public.pvz (id_pvz, address) VALUES (24, '344288, г. Лесной, ул. Чехова, 1');
INSERT INTO public.pvz (id_pvz, address) VALUES (25, '614164, г.Лесной,  ул. Степная, 30');
INSERT INTO public.pvz (id_pvz, address) VALUES (26, '394242, г. Лесной, ул. Коммунистическая, 43');
INSERT INTO public.pvz (id_pvz, address) VALUES (27, '660540, г. Лесной, ул. Солнечная, 25');
INSERT INTO public.pvz (id_pvz, address) VALUES (28, '125837, г. Лесной, ул. Шоссейная, 40');
INSERT INTO public.pvz (id_pvz, address) VALUES (29, '125703, г. Лесной, ул. Партизанская, 49');
INSERT INTO public.pvz (id_pvz, address) VALUES (30, '625283, г. Лесной, ул. Победы, 46');
INSERT INTO public.pvz (id_pvz, address) VALUES (31, '614753, г. Лесной, ул. Полевая, 35');
INSERT INTO public.pvz (id_pvz, address) VALUES (32, '426030, г. Лесной, ул. Маяковского, 44');
INSERT INTO public.pvz (id_pvz, address) VALUES (33, '450375, г. Лесной ул. Клубная, 44');
INSERT INTO public.pvz (id_pvz, address) VALUES (34, '625560, г. Лесной, ул. Некрасова, 12');
INSERT INTO public.pvz (id_pvz, address) VALUES (35, '630201, г. Лесной, ул. Комсомольская, 17');
INSERT INTO public.pvz (id_pvz, address) VALUES (36, '190949, г. Лесной, ул. Мичурина, 26');


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.users (id_user, fio, login, password, role) VALUES (1, 'Никифорова Весения Николаевна', '94d5ous@gmail.com', 'uzWC67', 'admin');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (2, 'Сазонов Руслан Германович', 'uth4iz@mail.com', '2L6KZG', 'admin');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (3, 'Одинцов Серафим Артёмович', 'yzls62@outlook.com', 'JlFRCZ', 'admin');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (4, 'Степанов Михаил Артёмович', '1diph5e@tutanota.com', '8ntwUp', 'manager');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (5, 'Ворсин Петр Евгеньевич', 'tjde7c@yahoo.com', 'YOyhfR', 'manager');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (6, 'Старикова Елена Павловна', 'wpmrc3do@tutanota.com', 'RSbvHv', 'manager');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (7, 'Михайлюк Анна Вячеславовна', '5d4zbu@tutanota.com', 'rwVDh9', 'client');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (8, 'Ситдикова Елена Анатольевна', 'ptec8ym@yahoo.com', 'LdNyos', 'client');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (9, 'Ворсин Петр Евгеньевич', '1qz4kw@mail.com', 'gynQMT', 'client');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (10, 'Старикова Елена Павловна', '4np6se@mail.com', 'AtnDjr', 'client');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (11, 'Белоусов Максим Алексеевич', 'max', '123', 'admin');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (13, 'Леонова Марина Игоревна', 'mara', 'lazygirl', 'client');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (12, 'Дрябина Татьяна Александровна', 'tank', '123456', 'manager');
INSERT INTO public.users (id_user, fio, login, password, role) VALUES (123, 'Test', 'Test', 'Test123', 'admin');


--
-- Name: orders_id_order_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orders_id_order_seq', 26, true);


--
-- Name: product_id_product_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.product_id_product_seq', 40, true);


--
-- Name: users_id_user_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_user_seq', 13, true);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id_order, id_product);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id_order);


--
-- Name: product product_article_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_article_key UNIQUE (article);


--
-- Name: product product_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_pkey PRIMARY KEY (id_product);


--
-- Name: pvz pvz_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pvz
    ADD CONSTRAINT pvz_pkey PRIMARY KEY (id_pvz);


--
-- Name: users users_login_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_login_key UNIQUE (login);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id_user);


--
-- Name: order_items order_items_id_order_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_id_order_fkey FOREIGN KEY (id_order) REFERENCES public.orders(id_order);


--
-- Name: order_items order_items_id_product_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_id_product_fkey FOREIGN KEY (id_product) REFERENCES public.product(id_product);


--
-- Name: orders orders_id_pvz_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_id_pvz_fkey FOREIGN KEY (id_pvz) REFERENCES public.pvz(id_pvz);


--
-- PostgreSQL database dump complete
--

\unrestrict qpeXAyLSswW2ib0PVZMPsMCoe5m4z7ClV6cgfO6EX2QrBxiwFjJh5foEVxdKhaj

