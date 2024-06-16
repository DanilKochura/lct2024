from flask import Flask, render_template
import pymysql
import json

app = Flask(__name__)


@app.route('/')
def main_processor():
    pts, ships = get_points_and_schedules()
    return render_template("index.html", pts=pts, ships=ships)


def get_points_and_schedules():
    conn = pymysql.connect(host='localhost', user='admin_admin', password='Admin1234', database='admin_lct')
    # Получение точек
    pts = []
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM graph")
        pts = []
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            pts.append({
                'name': row['point_name'],
                'id': row['id']
            })
    # Получение кораблей
    ships = []
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM schedules")
        pts = []
        schema = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            row = dict(zip(schema, row))
            pts.append(row)  # TODO Проверить работоспособность

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





if __name__ == '__main__':
    app.run()


