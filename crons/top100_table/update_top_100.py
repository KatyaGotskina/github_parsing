import os

import psycopg2
from psycopg2 import pool
import requests
from dotenv import load_dotenv


load_dotenv()
postgresql_pool = psycopg2.pool.SimpleConnectionPool(
    1,  # min
    20,  # max
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME')
)


update_top100_query = '''
INSERT INTO top100 (id, repo, owner, stars, forks, watchers, open_issues, language, position_cur)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE
    SET
        stars = EXCLUDED.stars,
        forks = EXCLUDED.forks,
        position_cur = EXCLUDED.position_cur,
        position_prev = CASE
                        WHEN (SELECT position_cur FROM top100 WHERE id = EXCLUDED.id) = EXCLUDED.position_cur THEN top100.position_prev
                        ELSE (SELECT position_cur FROM top100 WHERE id = EXCLUDED.id)
                    END,
        watchers = EXCLUDED.watchers,
        open_issues = EXCLUDED.open_issues;
'''

'''
Получение данных о репозиториях в уже нужном нам порядке, отсортированы в порядке убывания по кол-ву ввезд
Берем топ 100
'''
def fetch_github_repositories():
    url = 'https://api.github.com/search/repositories'
    params = {
        'q': 'stars',
        'sort': 'stars',
        'order': 'desc',
        'per_page': 100,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data['items']


def update_top100() -> None:
    connection = postgresql_pool.getconn()
    cursor = connection.cursor()
    try:
        data = fetch_github_repositories()
        data_for_top100 = [(
            (
                repo['id'],
                repo['full_name'],
                repo['owner']['login'],
                repo['stargazers_count'],
                repo['forks'],
                repo['watchers'],
                repo['open_issues'],
                repo['language'],
                index + 1
            )
        ) for index, repo in enumerate(data)]
        cursor.executemany(update_top100_query, data_for_top100)
        connection.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
        postgresql_pool.putconn(connection)
