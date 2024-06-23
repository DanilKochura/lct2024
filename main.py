import re

from flask import Flask, render_template, request, redirect
import pymysql
import json
import solver.solver

app = Flask(__name__)


@app.route('/')
def main_processor():
    pts, ships, icebreakers = get_points_and_schedules()
    return render_template("index.html", pts=pts, ships=ships, icebreakers=icebreakers)


def get_points_and_schedules():
    conn = pymysql.connect(host='localhost', user='admin_admin', password='Admin1234', database='admin_lct')

    # Получение кораблей
    ships = []
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM schedules")
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            ships.append(row)

    # Получение точек
    pts = []
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM graph")
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            pts.append(row)

    icebreakers = []
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM icebreakers")
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            icebreakers.append(row)
    # Закрытие соединения
    conn.close()

    return pts, ships, icebreakers


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
    print("request.form: ", request.form)
    current, extended, current_ib, extended_ib = parse_form(data=request.form)

    print("current_ib", current_ib)
    print("extended_ib", extended_ib)

    print("parse_form(data=request.form): ", parse_form(data=request.form))

    # exit()
    conn = pymysql.connect(host='localhost', user='admin_admin', password='Admin1234', database='admin_lct')
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
            # print(query)
            cursor.execute(query)

        for ship in extended:  # Новые корабли заносим в базу.
            print("ship", ship)
            query = f"""
                INSERT INTO schedules (ship_name, ice_class, velocity, start_point_id, end_point_id, date_start, status) 
                VALUES ("{ship['name']}", "{ship['ice_class']}", {ship['speed']}, {ship['from']}, {ship['to']}, "{ship['date']}", {ship.get('status', 0)})
            """
            print("query", query)
            cursor.execute(query)

        for ship in current_ib:
            query = f"""
                UPDATE 
                    icebreakers
                SET 
                    name="{ship['name']}", 
                    speed={ship['speed']}, 
                    start_point={ship['start_point']}, 
                    ice_class="{ship['ice_class']}", 
                    start_time="{ship['start_time']}",
                    status={ship.get('status', 0)} 
                WHERE 
                    id={ship['id']}
            """
            # print(query)
            cursor.execute(query)

        for ship in extended_ib:  # Новые корабли заносим в базу.
            print("ship", ship)
            query = f"""
                INSERT INTO icebreakers (name, speed, start_point, ice_class, start_time, status) 
                VALUES ("{ship['name']}", {ship['speed']}, {ship['start_point']}, "{ship['ice_class']}", "{ship['start_time']}", {ship.get('status', 0)})
            """
            print("query", query)
            cursor.execute(query)

    conn.commit()
    conn.close()
    solver.solver.solve_schedules()
    return redirect("/")


def parse_form(data):
    # Преобразовываем кривой формат, в котором фронт отдаёт формы, во что-то адекватное.

    pattern = re.compile(r'current\[(\d+)\]\[(.*?)\]')
    data_dict_current = {}
    for key, value in data.items():
        match = pattern.search(key)
        if match:
            index = int(match.group(1))
            dict_key = match.group(2)
            if index not in data_dict_current:
                data_dict_current[index] = {}
            data_dict_current[index][dict_key] = value
    current = [data_dict_current[index] for index in sorted(data_dict_current.keys())]

    pattern = re.compile(r'extended\[(\d+)\]\[(.*?)\]')
    data_dict_extended = {}
    for key, value in data.items():
        match = pattern.search(key)
        if match:
            index = int(match.group(1))
            dict_key = match.group(2)
            if index not in data_dict_extended:
                data_dict_extended[index] = {}
            data_dict_extended[index][dict_key] = value
    extended = [data_dict_extended[index] for index in sorted(data_dict_extended.keys())]

    pattern = re.compile(r'current_ib\[(\d+)\]\[(.*?)\]')
    data_dict_current_ib = {}
    for key, value in data.items():
        match = pattern.search(key)
        if match:
            index = int(match.group(1))
            dict_key = match.group(2)
            if index not in data_dict_current_ib:
                data_dict_current_ib[index] = {}
            data_dict_current_ib[index][dict_key] = value
    current_ib = [data_dict_current_ib[index] for index in sorted(data_dict_current_ib.keys())]

    pattern = re.compile(r'extended_ib\[(\d+)\]\[(.*?)\]')
    data_dict_extended_ib = {}
    for key, value in data.items():
        match = pattern.search(key)
        if match:
            index = int(match.group(1))
            dict_key = match.group(2)
            if index not in data_dict_extended_ib:
                data_dict_extended_ib[index] = {}
            data_dict_extended_ib[index][dict_key] = value
    extended_ib = [data_dict_extended_ib[index] for index in sorted(data_dict_extended_ib.keys())]

    return current, extended, current_ib, extended_ib




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

