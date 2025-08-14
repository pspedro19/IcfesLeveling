import os
import psycopg2

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'host.docker.internal'),
    'port': os.getenv('DB_PORT', '5433'),
    'database': os.getenv('DB_NAME', 'gameplay_db'),
    'user': os.getenv('DB_USER', 'gameplay'),
    'password': os.getenv('DB_PASSWORD', 'gameplay123'),
}


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    # preserve subjects; drop dependent questions first
    cur.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='questions') THEN
            EXECUTE 'TRUNCATE TABLE questions RESTART IDENTITY CASCADE';
          END IF;
          IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='topics') THEN
            EXECUTE 'TRUNCATE TABLE topics RESTART IDENTITY CASCADE';
          END IF;
        END $$;
    """)
    cur.close()
    conn.close()
    print('OK: Truncated questions and topics')


if __name__ == '__main__':
    main()


