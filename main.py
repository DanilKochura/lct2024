import re

from flask import Flask, render_template, request, redirect
import pymysql
import json

app = Flask(__name__)


@app.route('/')
def main_processor():
    pts, ships = get_points_and_schedules()
    return render_template("index.html", pts=pts, ships=ships)


def get_points_and_schedules():
    conn = pymysql.connect(host='localhost', user='admin_admin', password='Admin1234', database='admin_lct')

    # Получение кораблей
    ships = []
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM schedules")
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            ships.append(row)  # TODO Проверить работоспособность

    # Получение точек
    pts = []
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM graph")
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            pts.append(row)


    # Закрытие соединения
    conn.close()

    return pts, ships


@app.route('/api/getGraph')
def get_points_and_edges():
    # Подключение к базе данных
    conn = pymysql.connect(host='localhost', user='admin_admin', password='Admin1234', database='admin_lct')
    # conn = pymysql.connect(host='localhost', user='root', password='mJve9nuhEI', database='admin_lct')

    # Получение точек
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM graph")
        pts = []
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            pts.append({
                'coords': [float(row['longitude']), float(row['latitude'])],
                'name': row['point_name'],
                'rep_id': row['rep_id'],
                'id': row['id']
            })

    # Получение рёбер
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM edges")
        edges = []
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            edges.append({
                'points': [int(row['start_point']), int(row['end_point'])],
                'length': row['length']
            })

    # Закрытие соединения
    conn.close()

    # Вывод результата в формате JSON
    return json.dumps({'points': pts, 'edges': edges})


# Заготовить логику для обработки формы:
# Маршрут /api/refresh-routes
# POST-запрос
# Логика: для всех current-судов данные обновляются (поиск по id)
# Все суда extended добавляются в базу
# Формат данных
#
# Если поля статус нет, то статус = 0
@app.route("/api/refresh-routes", methods=['POST', 'GET'])
def refresh_routes():
    updates = request.form
    print("request.form: ", request.form)
    current = parse_form(data=request.form)
    extended = []
    print("parse_form(data=request.form): ", parse_form(data=request.form))
    conn = pymysql.connect(host='localhost', user='root', password='tester', database='admin_lct')
    with conn.cursor() as cursor:
        for ship in current:  # Для старых кораблей обновляем данные.
            query = f"""
                UPDATE 
                    schedules 
                SET 
                    ship_name="{ship['name']}", 
                    velocity={ship['speed']}, 
                    start_point_id={ship['from']}, 
                    end_point_id={ship['to']}, 
                    ice_class="{ship['ice_class']}", 
                    date_start="{ship['date']}",
                    status={ship.get('status', 0)} 
                WHERE 
                    id={ship['id']}
            """
            print(query)
            cursor.execute(query)

        for ship in extended:  # Новые корабли заносим в базу.
            query = f"""
                INSERT INTO schedules (ship_name, ice_class, velocity, start_point_id, end_point_id, date_start, status) 
                VALUES ("{ship['name']}", "{ship['ice_class']}", {ship['speed']}, {ship['from']}, {ship['to']}, "{ship['date']}", {ship.get('status', 0)})
            """
            cursor.execute(query)
    conn.commit()
    conn.close()
    return redirect("/")


def parse_form(data):
    # Преобразование списка кортежей в массив словарей
    pattern = re.compile(r'current\[(\d+)\]\[(.*?)\]')
    data_dict = {}

    for key, value in data.items():
        match = pattern.search(key)
        if match:
            index = int(match.group(1))
            dict_key = match.group(2)
            if index not in data_dict:
                data_dict[index] = {}
            data_dict[index][dict_key] = value

    return [data_dict[index] for index in sorted(data_dict.keys())]

# def parse_form(data):
#     result = {}
#     items = {}
#     for key in data:
#         print(key, data[key])
#         if key.startswith('current['):
#             # Извлекаем индекс и свойство из ключа
#             index = key.split('[')[1].split(']')[0]
#             property = key.split('[')[2].split(']')[0]
#
#             # Инициализация словаря для данного индекса, если он еще не инициализирован
#             if index not in result:
#                 result[index] = {}
#
#             # Присваивание значения свойству в словаре
#             result[index][property] = items[key]
#
#         # Опционально, преобразование ключей из строк в целые числа
#     result = {int(k): v for k, v in result.items()}
#     return result






if __name__ == '__main__':
    app.run(debug=True)

