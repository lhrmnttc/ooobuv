import os
import sys
import time
import psycopg2

host = os.getenv("DB_HOST", "db")
port = int(os.getenv("DB_PORT", "5432"))
name = os.getenv("DB_NAME", "shoe_store")
user = os.getenv("DB_USER", "shoe_user")
password = os.getenv("DB_PASSWORD", "")

for attempt in range(1, 11):
    try:
        with psycopg2.connect(
            host=host,
            port=port,
            dbname=name,
            user=user,
            password=password,
            connect_timeout=3
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """)
                count = cursor.fetchone()[0]
                print(f"OK: таблиц={count}")

        sys.exit(0)

    except psycopg2.OperationalError as error:
        print(f"Попытка {attempt}: {error}")
        time.sleep(3)

sys.exit(1)
