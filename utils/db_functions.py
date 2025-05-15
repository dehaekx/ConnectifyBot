import json
import os

import asyncpg

from config_data.config import HOST, DATABASE, USER, PORT, PASSWORD, DB_URI
from utils.copy_bot import bot
from keyboards import keyboards as K

db_pool = None

host = HOST
database = DATABASE
user = USER
port = PORT
password = PASSWORD
DATABASE_URL = DB_URI
ADMIN_ID = json.loads(os.getenv('ADMIN_ID'))


async def db_create():
    conn = await asyncpg.connect(user=user, password=password, host=host, port=port)
    try:
        await conn.execute(''' CREATE DATABASE dayvinchik ''')
    except Exception as e:
        pass
    await conn.execute('COMMIT')
    await conn.close()

    return


async def tables_create():
    conn = await asyncpg.connect(user=user, password=password, database=database, host=host, port=port)

    await conn.execute('''CREATE TABLE IF NOT EXISTS users (
                           user_id CHAR(15) PRIMARY KEY, 
                           username CHAR(32),
                           first_name CHAR(20),
                           last_name CHAR(36),
                           age INT,
                           gender CHAR(10),
                           location POINT,
                           city VARCHAR(50),
                           about_me TEXT,
                           interests TEXT,
                           who_like CHAR(50),
                           profile_photo_file_id VARCHAR(255),
                           profile_video_file_id VARCHAR(255),
                           registration_date TIMESTAMP,
                           is_blocked BOOLEAN DEFAULT FALSE,
                           main_in_life VARCHAR(255),
                           main_in_people VARCHAR(255),
                           smoking_attitude VARCHAR(255),
                           alcohol_attitude VARCHAR(255),
                           search_city VARCHAR(50)
                           )''')

    await conn.execute('''CREATE TABLE IF NOT EXISTS messages(
                           message_id SERIAL PRIMARY KEY,
                           sender_id CHAR(15),
                           receiver_id CHAR(15),
                           message_text TEXT,
                           FOREIGN KEY (sender_id) REFERENCES users(user_id),
                           FOREIGN KEY (receiver_id) REFERENCES users(user_id)
                           )''')

    await conn.execute('''CREATE TABLE IF NOT EXISTS likes(
                           like_id SERIAL PRIMARY KEY,
                           liker_id CHAR(15),
                           liked_id CHAR(15),
                           FOREIGN KEY (liker_id) REFERENCES users(user_id),
                           FOREIGN KEY (liked_id) REFERENCES users(user_id)
                           )''')

    await conn.execute('''CREATE TABLE IF NOT EXISTS friends(
                           friendship_id SERIAL PRIMARY KEY,
                           user1_id CHAR(15),
                           user2_id CHAR(15),
                           FOREIGN KEY (user1_id) REFERENCES users(user_id),
                           FOREIGN KEY (user2_id) REFERENCES users(user_id)
                           )''')

    await conn.execute('''CREATE TABLE IF NOT EXISTS blocks(
                           block_id SERIAL PRIMARY KEY,
                           blocker_id CHAR(15),
                           blocked_id CHAR(15),
                           FOREIGN KEY (blocker_id) REFERENCES users(user_id),
                           FOREIGN KEY (blocked_id) REFERENCES users(user_id)
                           )''')


    await conn.execute('''CREATE TABLE IF NOT EXISTS complaints (
                               complaint_id SERIAL PRIMARY KEY,
                               user_id CHAR(15),
                               complained_user_id CHAR(15),
                               reason TEXT,
                               status CHAR(20),
                               FOREIGN KEY (user_id) REFERENCES users(user_id),
                               FOREIGN KEY (complained_user_id) REFERENCES users(user_id)
                               )''')

    await conn.execute('''
            CREATE TABLE IF NOT EXISTS dislikes (
                dislike_id SERIAL PRIMARY KEY,
                disliker_id CHAR(15),
                disliked_id CHAR(15),
                FOREIGN KEY (disliker_id) REFERENCES users(user_id),
                FOREIGN KEY (disliked_id) REFERENCES users(user_id)
            );
        ''')

    await conn.execute('''
        CREATE TABLE IF NOT EXISTS additional_photos (
            user_id CHAR(15) PRIMARY KEY,
            profile_photo_file_id_2 VARCHAR(255),
            profile_photo_file_id_3 VARCHAR(255),
            collage_file_id VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    ''')

    await conn.execute('COMMIT')
    await conn.close()

    return


async def insert_user_id(user_id):
    async with db_pool.acquire() as conn:
        user_id = str(user_id)
        query = (
            "INSERT INTO users (user_id) VALUES ($1)"
        )

        await conn.execute(query, user_id)
        await conn.execute("COMMIT")
        await conn.close()


async def get_liker_user_id(liked_user_id):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT user_id, first_name, age, about_me, city FROM users WHERE user_id = (SELECT '
                                  'liker_id FROM likes WHERE liked_id = $1 ORDER BY like_id DESC LIMIT 1)',
                                  liked_user_id)
        user = dict(row) if row else None
    return user


async def check_user_exists(user_id):
    async with db_pool.acquire() as conn:
        user_id = str(user_id)
        query = "SELECT COUNT(*) FROM users WHERE user_id = $1"
        result = await conn.fetchval(query, user_id)
        return result > 0


async def check_user_fields_filled(user_id):
    async with db_pool.acquire() as conn:
        user_id = str(user_id)
        query = """
            SELECT first_name, last_name, age, city, who_like, interests, profile_photo_file_id, profile_video_file_id
            FROM users 
            WHERE user_id = $1
        """
        result = await conn.fetchrow(query, user_id)

        if not result:
            return False  # Если пользователя нет в базе

        # Проверяем, что обязательные поля не пустые
        required_fields = ["first_name", "last_name", "age", "city", "who_like", "interests"]
        for field in required_fields:
            if not result[field]:  # None или пустая строка
                return False

        # Проверяем, что есть хотя бы одно из profile_photo_file_id или profile_video_file_id
        if not (result["profile_photo_file_id"] or result["profile_video_file_id"]):
            return False

        return True  # Все обязательные поля заполнены



async def update_user(user_id, field_name, value):
    async with db_pool.acquire() as conn:
        query = (
            f"UPDATE users SET {field_name}=$1 WHERE user_id=$2"
        )

        await conn.execute(query, value, user_id)
        await conn.execute("COMMIT")
        await conn.close()


async def clear_user_columns(user_id):
    async with db_pool.acquire() as conn:
        # Define the columns to clear and their default values
        columns_to_clear = {
            'profile_photo_file_id': None,
            'profile_video_file_id': None,
            'about_me': '',  # Assuming this is a text column
            'interests': '',  # Assuming this is a text column
            'who_like': '',  # Assuming this is a text column
            'username': None,
            'first_name': None,
            'last_name': None,
            'age': None,
            'gender': None,
            'location': None,
            'city': None,
            'registration_date': None,
            'is_blocked': False,
        }

        # Construct the SQL query
        set_clause = ', '.join([f"{column} = ${i+1}" for i, column in enumerate(columns_to_clear)])
        query = f"UPDATE users SET {set_clause} WHERE user_id = ${len(columns_to_clear) + 1}"

        # Get the values to bind to the query
        values = list(columns_to_clear.values())
        values.append(user_id)

        # Execute the query
        await conn.execute(query, *values)
        await conn.execute("COMMIT")
        await conn.close()


async def delete_users_with_only_user_id():
    async with db_pool.acquire() as conn:
        # Define the columns to check for null or empty string values
        columns_to_check = [
            'profile_photo_file_id',
            'profile_video_file_id',
            'about_me',
            'interests',
            'who_like',
            'username',
            'first_name',
            'last_name',
            'age',
            'gender',
            'location',
            'city',
            'registration_date',
            'is_blocked'
        ]

        # Construct the SQL query
        where_clause = ' AND '.join([f"({column} IS NULL OR {column} = '')" for column in columns_to_check])
        query = f"DELETE FROM users WHERE {where_clause}"

        # Execute the query
        await conn.execute(query)
        await conn.execute("COMMIT")
        await conn.close()



async def profile_exists(user_id):
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', user_id)
        if user:
            return True
        else:
            return False


async def get_user_info(user_id):
    async with db_pool.acquire() as conn:
        user_info = await conn.fetchrow('SELECT first_name, age FROM users WHERE user_id=$1', user_id)
    return user_info


async def get_first_name_info(user_id):
    async with db_pool.acquire() as conn:
        first_name = await conn.fetchval('SELECT first_name FROM users WHERE user_id=$1', user_id)
    return first_name


async def get_age_info(user_id):
    async with db_pool.acquire() as conn:
        age = await conn.fetchval('SELECT age FROM users WHERE user_id=$1', user_id)
    return age


async def get_about_me(user_id):
    async with db_pool.acquire() as conn:
        about_me = await conn.fetchval('SELECT about_me FROM users WHERE user_id=$1', user_id)
    return about_me if about_me else "Информации нет"


async def get_city_info(user_id):
    async with db_pool.acquire() as conn:
        city = await conn.fetchval('SELECT city FROM users WHERE user_id=$1', user_id)
    return city


async def get_main_in_life(user_id):
    async with db_pool.acquire() as conn:
        main_in_life = await conn.fetchval('SELECT main_in_life FROM users WHERE user_id=$1', user_id)
    return main_in_life


async def get_main_in_people(user_id):
    async with db_pool.acquire() as conn:
        main_in_people = await conn.fetchval('SELECT main_in_people FROM users WHERE user_id=$1', user_id)
    return main_in_people


async def get_smoking_attitude(user_id):
    async with db_pool.acquire() as conn:
        smoking_attitude = await conn.fetchval('SELECT smoking_attitude FROM users WHERE user_id=$1', user_id)
    return smoking_attitude


async def get_alcohol_attitude(user_id):
    async with db_pool.acquire() as conn:
        alcohol_attitude = await conn.fetchval('SELECT alcohol_attitude FROM users WHERE user_id=$1', user_id)
    return alcohol_attitude


async def get_photo_file_id(user_id):
    async with db_pool.acquire() as conn:
        photo_file_id = await conn.fetchval('SELECT profile_photo_file_id FROM users WHERE user_id=$1', user_id)
    return photo_file_id


async def get_video_file_id(user_id):
    async with db_pool.acquire() as conn:
        video_file_id = await conn.fetchval('SELECT profile_video_file_id FROM users WHERE user_id=$1', user_id)
    return video_file_id


async def get_username(user_id):
    async with db_pool.acquire() as conn:
        username = await conn.fetchval('SELECT username FROM users WHERE user_id=$1', user_id)
    return username


async def get_friends_all(user_id):
    async with db_pool.acquire() as conn:
        query = '''
            SELECT u.first_name, COALESCE(u.username, '') AS username
            FROM friends AS f
            JOIN users AS u ON (f.user1_id = u.user_id AND f.user2_id = $1) 
                            OR (f.user2_id = u.user_id AND f.user1_id = $1)
            WHERE $1 IN (f.user1_id, f.user2_id)
        '''
        friends = await conn.fetch(query, user_id)
    return friends


async def delete_friend(user_id: str, friend_username: str):
    async with db_pool.acquire() as conn:
        friend_id_query = '''
            SELECT user_id FROM users WHERE username = $1
        '''
        friend_id = await conn.fetchval(friend_id_query, friend_username)

        if not friend_id:
            return False

        delete_query = '''
            DELETE FROM friends
            WHERE (user1_id = $1 AND user2_id = $2) OR (user1_id = $2 AND user2_id = $1)
        '''
        await conn.execute(delete_query, user_id, friend_id)
        return True


async def find_similar_users(user_id):
    query = """
        WITH user_info AS (
            SELECT search_city FROM users WHERE user_id = $1
        )
        SELECT 
            u2.user_id,
            COUNT(*) AS common_interests
        FROM users u1
        JOIN users u2 ON u1.user_id != u2.user_id
        JOIN user_info ui ON TRUE 
        JOIN LATERAL unnest(string_to_array(u1.interests, ',')) interest 
            ON interest = ANY(string_to_array(u2.interests, ','))
        WHERE 
            u1.user_id = $1
            AND u2.user_id != $1
            AND (
                (u1.who_like = 'man_and_woman_like')
                OR (u1.who_like = 'man_like' AND u2.gender = 'man')
                OR (u1.who_like = 'woman_like' AND u2.gender = 'woman')
            )
            AND (ui.search_city = 'all' OR u2.city = ui.search_city)
        GROUP BY u2.user_id
        ORDER BY common_interests DESC;
    """

    async with db_pool.acquire() as conn:
        similar_users = []
        async with conn.transaction():
            async for row in conn.cursor(query, user_id):
                similar_users.append(row['user_id'])
        return similar_users


async def check_like(liker_id: str, liked_id: str) -> bool:
    """Проверяет, поставил ли пользователь лайк другому пользователю."""
    query = """
        SELECT COUNT(*) 
        FROM likes 
        WHERE liker_id = $1 AND liked_id = $2
    """
    async with db_pool.acquire() as conn:
        count = await conn.fetchval(query, liker_id, liked_id)
        return count > 0


async def check_dislike(disliker_id: str, disliked_id: str) -> bool:
    """Проверяет, поставил ли пользователь дизлайк другому пользователю."""
    query = """
        SELECT COUNT(*) 
        FROM dislikes 
        WHERE disliker_id = $1 AND disliked_id = $2
    """
    async with db_pool.acquire() as conn:
        count = await conn.fetchval(query, disliker_id, disliked_id)
        return count > 0


async def get_user_interests(user_id):
    async with db_pool.acquire() as conn:
        query = '''
            SELECT interests
            FROM users
            WHERE user_id = $1
        '''
        row = await conn.fetchrow(query, user_id)
        print(f'row {row}')
        if row:
            interests = row['interests']
            return interests.split(',') if interests else []
        else:
            return []


async def put_like(liker_id: str, liked_id: str):
    """Добавляет лайк от пользователя liker_id пользователю liked_id в базу данных."""
    query = """
        INSERT INTO likes (liker_id, liked_id)
        VALUES ($1, $2)
        RETURNING liked_id
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(query, liker_id, liked_id)
        return result


async def put_dislike(disliker_id: str, disliked_id: str):
    """Добавляет дизлайк от пользователя disliker_id пользователю disliked_id в базу данных."""
    # Подключение к базе данных
    async with db_pool.acquire() as conn:
        # Выполнение запроса к базе данных для добавления дизлайка
        await conn.execute(
            """
            INSERT INTO dislikes (disliker_id, disliked_id)
            VALUES ($1, $2)
            """,
            disliker_id, disliked_id
        )


async def get_user_by_id(user_id: str):
    """Возвращает информацию о пользователе по его ID."""
    query = """
        SELECT *
        FROM users
        WHERE user_id = $1
    """

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(query, user_id)
        return dict(row) if row else None


async def get_unchecked_complaints():
    async with db_pool.acquire() as conn:
        complaints = await conn.fetch('SELECT complaint_id, user_id, complained_user_id, reason FROM complaints WHERE '
                                      'status = \'unchecked\' OR status IS NULL')
    return complaints


async def get_complaint_by_id(complaint_id: int):
    async with db_pool.acquire() as conn:
        complaint = await conn.fetchrow('SELECT * FROM complaints WHERE complaint_id = $1', complaint_id)
    return complaint


async def save_message(sender_id: str, receiver_id: str, message_text: str):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO messages (sender_id, receiver_id, message_text)
            VALUES ($1, $2, $3)
        ''', sender_id, receiver_id, message_text)


async def check_mutual_like(user_id: str, liked_user_id: str) -> bool:
    query = """SELECT COUNT(*) FROM likes WHERE liker_id = $1 AND liked_id = $2 AND liker_id IN (SELECT liked_id FROM 
    likes WHERE liker_id = $2 AND liked_id = $1)"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(query, user_id, liked_user_id)
        return result > 0


async def put_complaint(user_id: str, complained_user_id: str, reason: str, complained_username: str):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO complaints (user_id, complained_user_id, reason)
            VALUES ($1, $2, $3)
        ''', user_id, complained_user_id, reason)

        complaint_count = await conn.fetchval('''
            SELECT COUNT(*) FROM complaints WHERE complained_user_id = $1
        ''', complained_user_id)

        if complaint_count >= 5:
            for admin_id in ADMIN_ID:
                await bot.send_message(
                    admin_id,
                    f"Пользователь @{complained_username} накопил 5 или более жалоб.\n\n"
                    f"Выберите действие:",
                    reply_markup=await K.admin_keyboard_ban_decision(str(complained_user_id))
                )


async def accept_friend_request(user_id: str, friend_id: str):
    async with db_pool.acquire() as conn:
        # Проверяем, существуют ли оба пользователя
        user_exists = await conn.fetchval('SELECT EXISTS(SELECT 1 FROM users WHERE user_id=$1)', user_id)
        friend_exists = await conn.fetchval('SELECT EXISTS(SELECT 1 FROM users WHERE user_id=$1)', friend_id)

        if user_exists and friend_exists:
            # Проверяем, нет ли уже записи в friends
            existing_friendship = await conn.fetchval('''
                SELECT EXISTS(
                    SELECT 1 FROM friends
                    WHERE (user1_id = $1 AND user2_id = $2) 
                       OR (user1_id = $2 AND user2_id = $1)
                )
            ''', user_id, friend_id)

            if not existing_friendship:  # Если пары еще нет, добавляем
                await conn.execute('''
                    INSERT INTO friends (user1_id, user2_id)
                    VALUES ($1, $2)
                ''', user_id, friend_id)
            else:
                print(f"Запись уже существует: {user_id} - {friend_id}")
        else:
            print(f"User {user_id} or friend {friend_id} does not exist in the 'users' table.")


async def accept_reject_friend_request(user_id: str, friend_id: str):
    async with db_pool.acquire() as conn:
        request = await conn.fetchrow('''
            SELECT * FROM friend_requests
            WHERE user_id = $1 AND friend_id = $2
        ''', user_id, friend_id)
        if request:
            return True
        else:
            return False


async def add_friend(user_id: str, friend_id: str):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO friend_requests (user_id, friend_id)
            VALUES ($1, $2)
        ''', user_id, friend_id)


async def update_complaint_status_by_user_id(user_id: str, status: str):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE complaints
            SET status = $1
            WHERE complained_user_id = $2;
        ''', status, user_id)


async def get_complaint_by_user_id(user_id: str):
    async with db_pool.acquire() as conn:
        complaint = await conn.fetchrow('''
            SELECT * FROM complaints
            WHERE complained_user_id = $1;
        ''', user_id)
        return complaint


async def get_message_between_users(user1_id: str, user2_id: str):
    async with db_pool.acquire() as conn:
        query = '''
            SELECT message_text
            FROM messages
            WHERE (sender_id = $1 AND receiver_id = $2) OR (sender_id = $2 AND receiver_id = $1)
            ORDER BY message_id DESC
            LIMIT 1
        '''
        message = await conn.fetchval(query, user1_id, user2_id)
    return message


async def get_additional_photo_by_column(user_id: str, column_name: str):
    query = f"SELECT {column_name} FROM additional_photos WHERE user_id = '{user_id}';"
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            result = await conn.fetchval(query)
            return result


async def insert_user_id_additional_photo(user_id: str):
    async with db_pool.acquire() as conn:
        # Проверяем, существует ли уже запись для указанного user_id
        result = await conn.fetchrow('SELECT * FROM additional_photos WHERE user_id = $1', user_id)
        if not result:
            # Если записи не существует, вставляем новую запись с user_id
            await conn.execute('INSERT INTO additional_photos (user_id) VALUES ($1)', user_id)


async def update_additional_photo(user_id, field_name, value):
    async with db_pool.acquire() as conn:
        query = f'''
                UPDATE additional_photos
                SET {field_name} = $2
                WHERE user_id = $1;
                '''
        await conn.execute(query, user_id, value)


async def get_additional_photos(user_id: str):
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow('''
            SELECT *
            FROM additional_photos
            WHERE user_id = $1;
        ''', user_id)
        if result:
            return dict(result)
        else:
            return None


async def get_all_additional_photos(user_id: str) -> dict:
    query = f"SELECT u.profile_photo_file_id, a.profile_photo_file_id_2, a.profile_photo_file_id_3 " \
            f"FROM users u " \
            f"JOIN additional_photos a ON u.user_id = a.user_id " \
            f"WHERE u.user_id = '{user_id}';"
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            result = await conn.fetchrow(query)
            if result:
                return dict(zip(['profile_photo_file_id', 'profile_photo_file_id_2', 'profile_photo_file_id_3'], result))
            else:
                return {}


async def save_collage_file_id(user_id: str, collage_file_id: str):
    async with db_pool.acquire() as conn:
        await conn.execute('''
                UPDATE additional_photos
                SET collage_file_id = $2
                WHERE user_id = $1;
        ''', user_id, collage_file_id)


async def get_collage_file_id(user_id: str):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('''
                SELECT collage_file_id
                FROM additional_photos
                WHERE user_id = $1;
        ''', user_id)
        return row[0] if row else None


async def insert_block(blocker_id: str, blocked_id: str):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute('''
                INSERT INTO blocks (blocker_id, blocked_id)
                VALUES ($1, $2)
            ''', blocker_id, blocked_id)

            await conn.execute('''
                UPDATE users
                SET is_blocked = TRUE
                WHERE user_id = $1
            ''', blocked_id)

            await conn.execute('''
                UPDATE complaints
                SET status = 'resolved'
                WHERE complained_user_id = $1
            ''', blocked_id)


async def is_user_blocked(user_id: str):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('''
            SELECT is_blocked FROM users WHERE user_id = $1
        ''', user_id)
        return row and row['is_blocked']



async def get_all_blocked_users():
    async with db_pool.acquire() as conn:
        result = await conn.fetch('''
            SELECT blocked_id FROM blocks
        ''')
        return [row['blocked_id'] for row in result]


async def clear_user_photo_file_id(user_id: str):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE users
            SET profile_photo_file_id = NULL
            WHERE user_id = $1;
        ''', user_id)


async def clear_additional_photo_file_ids(user_id: str):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE additional_photos
            SET profile_photo_file_id_2 = NULL, profile_photo_file_id_3 = NULL, collage_file_id = NULL
            WHERE user_id = $1;
        ''', user_id)
