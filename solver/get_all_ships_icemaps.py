import json
import math

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import locale
from datetime import datetime, timedelta


# файл для расчет графа на минимальный путь для судна (см. ships.json)


# Установите локаль на русскую
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')



# Загрузка данных из файла Excel
file_path_graph = 'data/1ГрафДанные.xlsx'
file_path_schedule = 'data/Расписание.xlsx'
f = open('map.json')
file_edges = json.load(f)
print(file_edges)
points_df = pd.read_excel(file_path_graph, sheet_name='points')
edges_df = pd.read_excel(file_path_graph, sheet_name='edges')
schedule_df = pd.read_excel(file_path_schedule, sheet_name='Лист1')

#Создание словаря для поиска ID порта по его названию
port_name_to_id = {row['point_name']: row['point_id'] for _, row in points_df.iterrows()}
port_id_to_name = {row['point_id']: row['point_name'] for _, row in points_df.iterrows()}
port_id_to_coords = {row['point_id']: [row['longitude'], row['latitude']] for _, row in points_df.iterrows()}

# Преобразование координат для Берингова пролива справа
def transform_longitude(lon):
    return lon + 360 if lon < 0 else lon

points_df['longitude'] = points_df['longitude'].apply(transform_longitude)



icebreakers = [
    {
        'id': 1,
        'iceClass': 'Arc91',
        'name':  '50 лет Победы',
        'startPosition': 27,
        'speed': 22,
        'weights': {}
    },
    {
        'id': 2,
        'iceClass': 'Arc91',
        'name':  'Ямал',
        'startPosition': 41,
        'speed': 21,
        'weights': {}
    },
    {
        'id': 3,
        'iceClass': 'Arc92',
        'name':  'Таймыр',
        'startPosition': 16,
        'speed': 18.5,
        'weights': {}
    },
    {
        'id': 4,
        'iceClass': 'Arc92',
        'name':  'Вайгач',
        'startPosition': 6,
        'speed': 18.5,
        'weights': {}
    },
]



# Создание графа
G = nx.Graph()

# Добавление вершин
for _, row in points_df.iterrows():
    G.add_node(row['point_id'], pos=(row['longitude'], row['latitude']), label=row['point_name'])

edges = {}
# Добавление ребер
for _, row in edges_df.iterrows():
    G.add_edge(row['start_point_id'], row['end_point_id'], weight=file_edges[str(int(row['id']))])
    edges[(row['start_point_id'], row['end_point_id'])] = row['id']
# Получение позиций вершин
pos = nx.get_node_attributes(G, 'pos')
labels = nx.get_node_attributes(G, 'label')

# Функция для расчета времени в пути с учетом скорости судна
def calculate_travel_time(length, speed):
    return length

# Создание расписания с временем в пути
schedule_df['travel_time'] = schedule_df.apply(
    lambda row: calculate_travel_time(
        nx.shortest_path_length(
            G,
            source=port_name_to_id[row['Пункт начала плавания']],
            target=port_name_to_id[row['Пункт окончания плавания']],
            weight='length'
        ),
        row['Скорость']
    ),
    axis=1
)
ice = True
def create_weight_function(ice_class, speed):
    def get_edge_weight(u, v, attributes):
        return attributes['weight'][ice_class]['solo'] / speed
    return get_edge_weight
open('routes.txt', 'w').close()
# Создание функции веса с дополнительным параметром multiplier
# Создание расписания маршрутов для каждого судна
ship_routes = {}
ships = []
ships_test = []
iceb_ship = []
for _, row in schedule_df.iterrows():
    ship_name = row['Название судна']
    start_point = port_name_to_id[row['Пункт начала плавания']]
    end_point = port_name_to_id[row['Пункт окончания плавания']]
    speed = row['Скорость']
    ice_class = row['Ледовый класс'].replace(" ", '')
    if(ice_class == "Нет"): ice_class = "нет"
    if ship_name not in ship_routes:
        ship_routes[ship_name] = []
    start_date = row['Дата начала плавания']

    edges_ship = {}

    for edge in file_edges:
       edges_ship[int(edge)] = {'solo': file_edges[edge][ice_class]['solo'] / speed, 'provided': file_edges[edge][ice_class]['provided'] / speed}

    if ice:
       for ib in icebreakers:
           ispeed = ib['speed']
           for edge in file_edges:
               ib['weights'][int(edge)] = {'solo': file_edges[edge][ib['iceClass']]['solo'] / ispeed,
                                      'provided': file_edges[edge][ib['iceClass']]['provided'] / ispeed}
           iceb_ship.append(ib)
           ice = False

    ships_test.append({
        "name": ship_name,
        "speed": speed,
        "iceClass": ice_class,
        "route": [start_point, end_point],
        "weights": edges_ship,
        "departure_time": start_date.strftime("%Y-%m-%d") # Время отплытия судна
    })


    weight_function = create_weight_function(ice_class, speed)
    route = nx.shortest_path(G, source=start_point, target=end_point, weight=weight_function)

    total_distance = nx.shortest_path_length(G, source=start_point, target=end_point, weight=weight_function)
    travel_time = calculate_travel_time(total_distance, speed)
    if(math.isinf(travel_time)):
        travel_time = 1000000
    ship_routes[ship_name].append((route, start_date, start_date + pd.Timedelta(hours=travel_time)))

    # Исходная строка
    date_str = row['Дата начала плавания']
    print(date_str)
    # Удаляем 'г.' из строки

    true_route = []
    iter = 0
    formatted_date = date_str.strftime("%Y-%m-%d")
    true_route.append({
        'port': int(route[0]),
        'coords': port_id_to_coords[route[0]],
        'port_name': port_id_to_name[route[0]],
        'date': formatted_date,
        'time': 0
    })
    date_new = date_str
    for i in route:
        iter += 1
        if iter == 1: continue
        if (int(route[iter-2]), (int(i))) in edges:
            edge_id = edges[(int(route[iter-2]), (int(i)))]
        else:
            edge_id = edges[((int(i)), int(route[iter-2]))]
        av_time = 0
        time = file_edges[str(int(edge_id))][ice_class]['solo']
        if (math.isinf(time)):
            time = 10000000
            date_new = date_new + timedelta(days=100)
            av_time = time
        else:
            date_new = date_new + timedelta(seconds=int(time * 60 * 60 / speed))
            av_time = time / speed

        true_route.append({
            'port': int(i),
            'coords': port_id_to_coords[i],
            'port_name': port_id_to_name[i],
            'date': date_new.strftime('%Y-%m-%d %H:%M:%S'),
            'time': av_time
        })

    # Форматируем дату в нужном формате
    print(true_route)
    # Вывод маршрута и общего времени плавания корабля в консоль
    ships.append({"name": ship_name, "route": true_route, "speed": speed, "date": formatted_date})
    route_points = [points_df.loc[points_df['point_id'] == point, 'point_name'].values[0] for point in route]
    with open('routes.txt', 'r+') as f:
        f.seek(0, 2)  # перемещение курсора в конец файла
        f.write(f"Маршрут для {ship_name}: {' -> '.join(route_points)} (Total travel time: {travel_time} hours)\n")  # собственно, запись
        f.close()
    print(f"Маршрут для {ship_name}: {' -> '.join(route_points)} (Total travel time: {travel_time} hours)")

# Рисование графа перед анимацией
fig, ax = plt.subplots(figsize=(10, 10))
nx.draw(G, pos, node_color='blue', node_size=200, labels=labels, with_labels=True, ax=ax)
print(json.dumps(ships))
json_file_path = "test/ships.json"
with open(json_file_path, 'w') as json_file:
    json.dump(ships, json_file, indent=4, ensure_ascii=False)

json_file_path = "../test/icebreakers.json"
with open(json_file_path, 'w') as json_file:
    json.dump(iceb_ship, json_file, indent=4, ensure_ascii=False)

# Функция для анимации одного корабля
json_file_path = "../test/ships_test.json"
with open(json_file_path, 'w') as json_file:
    json.dump(ships_test, json_file, indent=4, ensure_ascii=False)