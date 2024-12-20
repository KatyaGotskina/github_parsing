from datetime import datetime, timedelta, date
import os
from typing import Union

import psycopg2
from dotenv import load_dotenv
from psycopg2 import pool
import requests
import arrow


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

update_activity_sql = """
INSERT INTO activity (git_id, date, authors, commits)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (git_id, date) DO UPDATE SET
        commits = EXCLUDED.commits,
        authors = EXCLUDED.authors
"""

# переменные для более понятной аннотации
commit_id = str
commit_date = date
commits_count = int
commit_author = str

"""
Получение данных о репозиториях: id, имя, владелец
Решила сделать запрос к этому API вместо select запроса из таблицы top100, 
поскольку у гитхаба есть лимит заросов, и select может быть избыточным.
Запрос аналогичный запросу для обновления top100, чтобы получать данные о коммитах нужных нам репозиториев
"""
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


"""
Описанную ниже структуру commits_data, перевожу в кортеж для множественнного инсерта в таблицу activity
"""
def activity_to_tuple_for_insert(
        data: dict[commit_id, dict[commit_date, Union[dict[str, set[commit_author]], dict[str, commits_count]]]]
) -> list[tuple[commit_id, commit_date, list[commit_author], commits_count]]:
    data_for_activity = []
    for repo_id, info in data.items():
        for date, other in info.items():
            data_for_activity.append((repo_id, date, list(other['authors']), other['commits_count']))
    return data_for_activity


"""
Я храню собранные данные в виде следующего словаря:
commits_data = {
    git_id: {
        date: {
            authors: set
            commits_count: int
            shas: set (
            Храню для проверки, что информация о коммите уже была получена и данные уже учитывают его наличие.
            Актуально при частых вызовах функции, когда данные в github не поменялись и response одинаковый
            )
        }
    }
}
Это помогает без лишних проверок структурировать данные 
"""
def update_activity():
    commits_data = {}
    connection = postgresql_pool.getconn()
    cursor = connection.cursor()
    try:
        for repo in fetch_github_repositories():
            '''
            Поскольку функция вызывается каждый день по несколько раз, 
            запрос данных, начиная со вчерашнего дня, является болле чем достаточным. 
            Выбрала такой вариант, потому что у github есть ограничение по запросам, 
            так что более ранняя дата только быстрее их израсходует
            '''
            yesterday = arrow.utcnow().shift(days=-1)
            commits_url = f"https://api.github.com/repos/{repo['owner']['login']}/{repo['name']}/commits"
            params = {
                # Максимально возможное кол-во данных на странице, чтобы минимизировать кол-во запросов
                'per_page': 100,
                'since': yesterday.format("YYYY-MM-DDTHH:mm:ssZ")
            }
            # Пока у запроса есть следующие страницы
            while commits_url:
                response = requests.get(commits_url, params=params)
                response.raise_for_status()
                for commit in response.json():
                    # Далее работа со структурой commits_data, о которой писала выше
                    date = arrow.get(commit['commit']['author']['date']).datetime.date()
                    repo_id, author, sha = repo['id'], commit['commit']['author']['name'], commit['sha']
                    commits_data.setdefault(repo_id, {}).setdefault(date, {}).setdefault('authors', set()).add(author)
                    # Проверка обрабатывала ли я уже коммит, о которой писала выше
                    if sha not in commits_data[repo_id][date].get('shas', set()):
                        commits_data[repo_id][date]['commits_count'] = (
                           commits_data[repo_id][date]
                           .get('commits_count', 0)
                       ) + 1
                    commits_data.setdefault(repo_id, {}).setdefault(date, {}).setdefault('shas', set()).add(sha)
                commits_url = response.links.get('next', {}).get('url')

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            data_for_activity = activity_to_tuple_for_insert(commits_data)
            cursor.executemany(update_activity_sql, data_for_activity)
            connection.commit()
            reset_timestamp = e.response.headers.get('X-RateLimit-Reset')
            print(f"Rate limit reset timestamp: {datetime(1970, 1, 1) + timedelta(seconds=int(reset_timestamp))}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
        postgresql_pool.putconn(connection)
