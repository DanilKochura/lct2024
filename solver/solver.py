import heapq
import itertools
import json
import locale
import random
import sys
import time
from copy import deepcopy
from operator import itemgetter
from time import sleep

import networkx as nx
from datetime import datetime, timedelta
from collections import deque

from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from sortedcontainers import SortedList
from matplotlib.backends.backend_pdf import PdfPages

from solver.DB import DB

def solve_schedules():
    all_times = []
    HOURS_FOR_WAIT = 36

    test = '/test'
    # test = ''

    def get_all_data():
        # Установите локаль на русскую
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

        db = DB()
        schedule_df = []
        result, schema = db.query("SELECT * from schedules where status = 1")
        for row in result:
            schedule_df.append(dict(zip(schema, row)))

        port_name_to_id = {}
        port_id_to_name = {}
        port_id_to_coords = {}
        points = []
        result, schema = db.query("SELECT * from graph")
        for row in result:
            row = dict(zip(schema, row))
            port_name_to_id[row['point_name']] = row['id']
            port_name_to_id[row['id']] = row['point_name']
            port_name_to_id[row['id']] = [row['longitude'], row['latitude']]
            points.append(row)
        print(schedule_df)
        # Загрузка данных из файла Excel
        # file_path_graph = 'data/1ГрафДанные.xlsx'
        # file_path_schedule = 'data/Расписание.xlsx'
        sheets = open('static/icemaps' + test + '/sheets.json')
        sheets = json.load(sheets)
        shits_list = {}
        for sheet in sheets:
            shits_list[sheet] = sheet
        # f = open('icemaps/map_02.04.2020.json')
        # f = open('map.json')
        # f_ice = open('icemaps/map_ice_03.03.2020.json')
        # f_ice = open('map.json')
        file_edges = {}
        file_edges_ice = {}
        for date_raw, date_form in shits_list.items():
            f = open('static/icemaps' + test + '/ships/map_' + date_form + '.json')
            f_ice = open('static/icemaps' + test + '/icebreakers/map_' + date_form + '.json')
            file_edges[date_form] = json.load(f)
            file_edges_ice[date_form] = json.load(f_ice)

        # points_df = pd.read_excel(file_path_graph, sheet_name='points')
        # edges_df = pd.read_excel(file_path_graph, sheet_name='edges')
        # schedule_df = pd.read_excel(file_path_schedule, sheet_name='Лист1')

        # Создание словаря для поиска ID порта по его названию
        # port_name_to_id = {row['point_name']: row['point_id'] for _, row in points_df.iterrows()}
        # port_id_to_name = {row['point_id']: row['point_name'] for _, row in points_df.iterrows()}
        # port_id_to_coords = {row['point_id']: [row['longitude'], row['latitude']] for _, row in points_df.iterrows()}
        #
        # Преобразование координат для Берингова пролива справа
        def transform_longitude(lon):
            return lon + 360 if lon < 0 else lon

        # points_df['longitude'] = points_df['longitude'].apply(transform_longitude)

        icebreakers = []
        result, schema = db.query("SELECT * from icebreakers where status = 1")
        for row in result:
            row = dict(zip(schema, row))
            icebreakers.append({
                'id': row['id'],
                'name': row['name'],
                'iceClass': row['ice_class'],
                'startPosition': row['start_point'],
                'startTime': row['start_time'],
                'speed': row['speed'],
                'route': [],
                'weights': {}
            })

        # icebreakers = [
        #     {
        #         'id': 1,
        #         'iceClass': 'Arc91',
        #         'name': '50 лет Победы',
        #         'startPosition': 27,
        #         'startTime': "2022-02-27 00:00:00",
        #         'speed': 22,
        #         'weights': {}
        #     },
        #     {
        #         'id': 2,
        #         'iceClass': 'Arc91',
        #         'name': 'Ямал',
        #         'startPosition': 41,
        #         'startTime': "2022-02-27 00:00:00",
        #         'speed': 21,
        #         'weights': {}
        #     },
        #     {
        #         'id': 3,
        #         'iceClass': 'Arc92',
        #         'name': 'Таймыр',
        #         'startPosition': 16,
        #         'startTime': "2022-02-27 00:00:00",
        #         'speed': 18.5,
        #         'weights': {}
        #     },
        #     {
        #         'id': 4,
        #         'iceClass': 'Arc92',
        #         'name': 'Вайгач',
        #         'startPosition': 6,
        #         'startTime': "2022-02-27 00:00:00",
        #         'speed': 18.5,
        #         'weights': {}
        #     },
        # ]

        # Функция для расчета времени в пути с учетом скорости судна

        # Функция для расчета времени в пути с учетом скорости судна
        def calculate_travel_time(length, speed):
            return length

        ice = True

        def create_weight_function(ice_class, speed):
            def get_edge_weight(u, v, attributes):
                return attributes['weight'][ice_class]['solo'] / speed

            return get_edge_weight

        # Создание функции веса с дополнительным параметром multiplier
        # Создание расписания маршрутов для каждого судна
        ship_routes = {}
        ships = []
        ships_test = []
        iceb_ship = []
        for row in schedule_df:
            ship_name = row['ship_name']
            start_point = row['start_point_id']
            end_point = row['end_point_id']
            speed = row['velocity']
            ice_class = row['ice_class'].replace(" ", '')
            if (ice_class == "Нет"): ice_class = "нет"
            if ship_name not in ship_routes:
                ship_routes[ship_name] = []
            start_date = row['date_start']

            edges_ship = {}

            for sheet in shits_list.values():
                for key, edge in file_edges[sheet].items():
                    if not edges_ship.get(sheet):
                        edges_ship[sheet] = {}
                    edges_ship[sheet][int(key)] = {'solo': edge[ice_class]['solo'] / speed,
                                                   'provided': edge[ice_class]['provided'] / speed}

            ships.append({
                "name": ship_name,
                "speed": speed,
                "iceClass": ice_class,
                "route": [start_point, end_point],
                "weights": edges_ship,
                "departure_time": start_date.strftime("%Y-%m-%d") + " 00:00:00",  # Время отплытия судна
                "id": row['id']
            })

        for ib in icebreakers:
            for sheet in shits_list.values():
                ispeed = ib['speed']
                for key, edge in file_edges_ice[sheet].items():
                    if not ib['weights'].get(sheet):
                        ib['weights'][sheet] = {}
                    ib['weights'][sheet][int(key)] = {
                        'solo': edge[ib['iceClass']]['ice'] + edge[ib['iceClass']]['clear'] / ispeed,
                        'provided': edge[ib['iceClass']]['ice'] + edge[ib['iceClass']]['clear'] / ispeed
                    }
                    #
                    # ib['weights'][sheet][int(key)] = {'solo': file_edges[sheet][key][ib['iceClass']]['solo'] / ispeed,
                    #                             'provided': file_edges[sheet][key][ib['iceClass']]['provided'] / ispeed}
            iceb_ship.append(ib)

        # json_file_path = "maps/ships.json"
        # with open(json_file_path, 'w', encoding="utf-8") as json_file:
        #     json.dump(ships, json_file, indent=4, ensure_ascii=False)
        #
        # json_file_path = "maps/icebreakers.json"
        # with open(json_file_path, 'w', encoding="utf-8") as json_file:
        #     json.dump(iceb_ship, json_file, indent=4, ensure_ascii=False)
        return ships, iceb_ship

    # Создать пустую кучу
    queue = SortedList(key=lambda x: x['departure_time'])

    # Добавление элементов в кучу (вставка с сохранением свойства кучи)
    def dynamic_weight_shortest_path(G, source, target, edge_weights):
        """
        Находит кратчайший путь на графе с динамическими весами рёбер.

        Args:
        - G (nx.Graph): Граф, по которому ищется путь.
        - source (node): Начальная вершина.
        - target (node): Конечная вершина.
        - edge_weights (dict): Словарь с весами рёбер, ключи — кортежи (u, v).

        Returns:
        - list: Кратчайший путь от source до target.
        """
        # Функция для вычисления веса ребра
        def get_edge_weight(u, v, data):
            edge_id = data['id']  # Предполагаем, что идентификатор ребра хранится в атрибуте 'id'
            return edge_weights.get(str(edge_id), float('inf'))

        # Вычисление кратчайшего пути с динамическими весами
        path = nx.shortest_path(G, source=source, target=target, weight=get_edge_weight)
        return path

    def dynamic_weight_shortest_path_length(G, source, target, edge_weights):
        """
        Находит кратчайший путь на графе с динамическими весами рёбер.

        Args:
        - G (nx.Graph): Граф, по которому ищется путь.
        - source (node): Начальная вершина.
        - target (node): Конечная вершина.
        - edge_weights (dict): Словарь с весами рёбер, ключи — кортежи (u, v).

        Returns:
        - list: Кратчайший путь от source до target.
        """

        # Функция для вычисления веса ребра
        def get_edge_weight(u, v, data):
            edge_id = data['id']  # Предполагаем, что идентификатор ребра хранится в атрибуте 'id'
            w = edge_weights.get(str(edge_id))
            return edge_weights.get(str(edge_id), float('inf'))

        # Вычисление кратчайшего пути с динамическими весами
        path = nx.shortest_path_length(G, source=source, target=target, weight=get_edge_weight)
        return path

    # Загрузка данных
    def load_json_data(filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)

    def random_date(start, end):
        """
        This function will return a random datetime between two datetime
        objects.
        """
        delta = end - start
        int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
        random_second = random.randrange(int_delta)
        return start + timedelta(seconds=random_second)

    def compare_routes(start, end, second_start, second_end, weight_first, weight_second):
        # second_path = nx.shortest_path(G, source=second_start, target=second_end, weight='weight')
        weight_1_tmp = weight_2_tmp = {}
        for eid, weights in weight_first.items():
            weight_1_tmp[eid] = weights['provided']
        weight_first = weight_1_tmp
        for eid, weights in weight_second.items():
            weight_2_tmp[eid] = weights['provided']
        weight_second = weight_2_tmp

        second_path = dynamic_weight_shortest_path(G, second_start, second_end, weight_second)
        path_common, path_to, path_after = find_paththrough(start, end, second_start, weight_first, weight_second)
        cross = []
        i = 0
        # print(points[str(start)]['name'], points[str(end)]['name'], points[str(second_start)]['name'], points[str(second_end)]['name'])
        # print(second_path, path_after, path_common, path_to)
        for crossing in second_path:
            if i == len(path_after) - 1: break
            if crossing == path_after[i]:
                cross.append(crossing)
            else:
                break
            i += 1
        if len(cross) > 1:
            clear_path = nx.shortest_path(G, source=start, target=cross[-1])
        else:
            clear_path = []

        class ComplexPath:
            def __init__(self, path_common, path_to, path_after, second_path, cross, clear_path):
                self.path_common = path_common  # цельный общий маршрут
                self.path_after = path_after  # путь каравана после встречи
                self.cross = cross  # общий путь в караване
                self.second_path = second_path  # полный путь второго
                self.path_to = path_to  # путь до места встречи
                self.clear_path = clear_path  # путь ледокола в чистую, ьез захода

        return ComplexPath(path_common, path_to, path_after, second_path, cross, clear_path)

    def find_paththrough(start_location, end_location, through_location, weight_start, weight_second):
        path_to_through = dynamic_weight_shortest_path(G, start_location, through_location, weight_start)
        pathh_to_end = dynamic_weight_shortest_path(G, through_location, end_location, weight_second)
        return path_to_through + pathh_to_end[1:], path_to_through, pathh_to_end

    def find_path_time(path, ships, date, key="provided"):
        times = {}
        for ship in ships:
            times[ship["id"]] = 0
            for id, edge in enumerate(path):
                if id == 0: continue
                times[ship["id"]] += ship['weights'][get_weights_period(date)][edge_id][key]
        return times

    def find_nearest_icebreaker(port, endpoint, icebreaker_queue, ship):
        """
        Находит ближайший ледокол к указанному порту.
        """
        min_distance = datetime.max
        nearest_icebreaker = None
        nearest_port = None
        total_to_end = 0
        time_for_ship = float('inf')

        for start_port, icebreaker in icebreaker_queue.items():
            if icebreaker:
                test = start_port
                weights_ice = {}
                time_slice = get_weights_period(icebreaker[0]['startTimestamp'])
                for eid, weights in icebreaker[0]['weights'][time_slice].items():
                    weights_ice[str(eid)] = weights['solo']

                # path_to_destination = nx.shortest_path(G, source=start_port, target=port, weight='weight')
                path_to_destination = dynamic_weight_shortest_path(G, start_port, port, weights_ice)
                time_to_port = 0
                time_to_port = dynamic_weight_shortest_path_length(G, start_port, port, weights_ice)
                if (time_to_port == float('inf')): continue
                time_to_end = dynamic_weight_shortest_path_length(G, port, endpoint, weights_ice)

                time_slice = get_weights_period(icebreaker[0]['startTimestamp']+timedelta(time_to_port))
                weights_ice = {}
                for eid, weights in ship['weights'][time_slice].items():
                    weights_ice[str(eid)] = weights['provided']
                # if(time_to_end == float('inf')): continue
                time_for_ship = dynamic_weight_shortest_path_length(G, port, endpoint, weights_ice)

                distance = datetime.strptime(icebreaker[0]['startTime'], "%Y-%m-%d %H:%M:%S") + timedelta(
                    hours=time_to_port)
                dprint(
                    icebreaker[0]['name'] + " " + points[str(start_port)]['name'] + " " + distance.strftime(
                        "%Y-%m-%d %H:%M:%S"))
                if distance < min_distance:
                    min_distance = distance
                    nearest_icebreaker = icebreaker[0]
                    nearest_port = start_port
                    total_to_end = time_to_end
                    time_for_ship = time_for_ship

        return nearest_icebreaker, nearest_port, min_distance, time_to_port, total_to_end, time_for_ship

    # Перемещаем ледокол от начальной точки до конечной, обновляя маршрут и время
    def move_icebreaker(icebreaker, start, end):
        """
        Перемещает ледокол от начальной точки до конечной, обновляя маршрут и время.
        """
        # path = nx.shortest_path(G, source=start, target=end, weight='weight')
        weights_ice = {}

        for eid, weights in icebreaker['weights'][get_weights_period(icebreaker['startTimestamp'])].items():
            weights_ice[eid] = weights['provided']
        path = dynamic_weight_shortest_path(G, start, end, weights_ice)
        if not icebreaker.get('route'):
            icebreaker['route'] = [
                {
                    "port": icebreaker['startPosition'],
                    "coords": points[str(icebreaker['startPosition'])]["coords"],
                    "port_name": points[str(icebreaker['startPosition'])]["name"],
                    "date": icebreaker['startTime'],
                    "time": 0,
                    "convoy": []
                }
            ]
        icebreaker_start_time = datetime.strptime(icebreaker['startTime'], "%Y-%m-%d %H:%M:%S")
        dprint("Собираюсь начать движение е судну", icebreaker_start_time)
        for idx, point in enumerate(path):
            if idx == 0:
                continue
            prev_point = path[idx - 1]
            edge_id = G.get_edge_data(prev_point, point)['id']
            icebreaker_edge_weight = icebreaker["weights"][get_weights_period(icebreaker_start_time)][edge_id]["solo"]
            if (icebreaker_edge_weight > 1000): break

            icebreaker_start_time += timedelta(hours=icebreaker_edge_weight)

            dprint("Первое перемещение " + points[str(prev_point)]['name'] + " - " + points[str(point)]['name'],
                   icebreaker_start_time)

            icebreaker['route'].append({
                "port": point,
                "coords": points[str(point)]["coords"],
                "port_name": points[str(point)]["name"],
                "date": icebreaker_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "time": icebreaker_edge_weight,
                "convoy": []
            })
            test = 1
        icebreaker['startPosition'] = end
        icebreaker['startTime'] = icebreaker_start_time.strftime("%Y-%m-%d %H:%M:%S")
        return icebreaker

    edges = load_json_data('static/test/edges.json')
    points = load_json_data('static/test/points_upd.json')
    ships_data, icebreakers_data = get_all_data()
    sheeets = json.load(open('static/icemaps' + test + '/sheets.json'))
    sheets_dates = {}
    for shit in sheeets:
        sheets_dates[datetime.strptime(shit + ' 00:00:00', "%d.%m.%Y %H:%M:%S")] = shit
    # ships_data = load_json_data('test/ships_hard.json')
    DEBUG = False
    sleep_timeout = 1
    if len(sys.argv) > 1:
        DEBUG = True

    if len(sys.argv) > 2:
        sleep_timeout = int(sys.argv[2])

    def dprint(string, time=False):
        if (DEBUG):
            if time:
                print(time.strftime("%Y-%m-%d %H:%M:%S") + " - " + str(string))
            else:
                print(string)

    # Создание графа
    G = nx.Graph()
    for edge in edges.values():
        point1, point2 = edge['points']
        length = float(edge['length'])
        G.add_edge(point1, point2, weight=length, id=edge['id'])

    ice_times = {}

    # Очередь заявок на проводку
    ship_requests = deque()
    ships_data = sorted(ships_data, key=lambda d: d['departure_time'])

    total_ships_time = 0
    total_ships_wait = 0
    total_ice_wait = 0
    sdata = ships_data
    # Инициализация всех возможных портов в icebreaker_queue
    all_ports = set()
    for edge in edges.values():
        point1, point2 = edge['points']
        all_ports.add(point1)
        all_ports.add(point2)

    min_common_time = float('inf')
    min_routes = []
    min_i = 0

    # hours = {ship['id']: [i for i in range(100)] for ship in ships_data}

    def time_of_function(function):
        def wrapped(*args):
            start_time = time.perf_counter_ns()
            res = function(*args)
            print(f"Время выполнения {function.__name__}:", time.perf_counter_ns() - start_time)
            return res

        return wrapped

    i = 0;

    def get_weights_period(date):
        date_tmp = '03.03.2022'
        for ts, shit in sheets_dates.items():
            if (ts > date):
                break
            date_tmp = shit

        return date_tmp

    for hours_to_wait in range(0, 100, 100):
        i += 1
        all_routes = {}
        print(i)
        icebreaker_queue = {port: deque() for port in all_ports}

        # Добавляем ледоколы в их начальные позиции в очереди
        for icebreaker in icebreakers_data:
            icebreaker['startTimestamp'] = icebreaker['startTime']
            icebreaker['startTime'] = icebreaker['startTime'].strftime("%Y-%m-%d %H:%M:%S")
            icebreaker_queue[icebreaker['startPosition']].append(icebreaker)
            ice_times[icebreaker['id']] = icebreaker['startTime']

        # Инициализация маршрутов ледоколов и судов
        icebreaker_routes = []
        ship_routes = {ship['name']: {
            "name": ship['name'],
            "type": "ship",
            "id": ship['id'],
            "ice_class": ship['iceClass'],
            "route": [
                {
                    "port": ship["route"][0],
                    "coords": points[str(ship["route"][0])]["coords"],
                    "port_name": points[str(ship["route"][0])]["name"],
                    "date": ship['departure_time'],
                    "time": 0,
                    "provided": False,
                    "waiting": False
                }
            ],
            "speed": ship['speed'],
            "date": ship['departure_time']
        } for ship in sdata}

        # Добавление всех судов в очередь заявок
        for ship in sdata:
            queue.add({
                "name": ship['name'],
                "start": ship["route"][0],
                "id": ship["id"],
                "end": ship["route"][1],
                "departure_time": datetime.strptime(ship['departure_time'], "%Y-%m-%d %H:%M:%S"),
                "current_time": datetime.strptime(ship['departure_time'], "%Y-%m-%d %H:%M:%S"),
                "route": ship["route"]
            })
            ship_requests.append({
                "name": ship['name'],
                "start": ship["route"][0],
                "id": ship["id"],
                "end": ship["route"][1],
                "departure_time": datetime.strptime(ship['departure_time'], "%Y-%m-%d %H:%M:%S"),
                "current_time": datetime.strptime(ship['departure_time'], "%Y-%m-%d %H:%M:%S"),
                "route": ship["route"]
            })

        # Словарь для отслеживания назначенных ледоколов
        assigned_icebreakers = {ship['name']: None for ship in sdata}

        ships_data = {x['id']: x for x in sdata}

        while queue:

            prov_counter = 0
            solo_counter = 0

            request = queue.pop(0)
            ship = ships_data[request['id']]
            ship_name = request['name']
            ship_start = request['start']
            # print(ship_name)
            # print(len(queue))
            ship_end = request['end']
            ship_departure_time = request['departure_time']
            ship_current_time = request['current_time']
            ship_route = request['route']
            if DEBUG:
                print('___________________')
                print(ship_name)
                sleep(sleep_timeout)

            if ship_start == ship_end:
                continue
            icebreaker = None
            if ship_start in icebreaker_queue and icebreaker_queue[ship_start] and False:
                icebreaker = icebreaker_queue[ship_start].popleft()
            else:
                icebreaker, nearest_port, time_for_icebreaker, time_to_port, total_to_end, time_for_ship = find_nearest_icebreaker(
                    ship_start, ship_end,
                    icebreaker_queue, ship)

                # if(total_to_end == float('inf')):
                #     dprint("Не, мы не доплывем")
                #     queue.add({
                #         "name": ship_name,
                #         "start": ship_start,
                #         "id": ship['id'],
                #         "end": ship_end,
                #         "departure_time": ship_current_time+timedelta(days=3),
                #         "current_time": ship_current_time+timedelta(days=3),
                #         "route": ship_route
                #     })
                #     continue
                dprint("Пытаюсь понять, могу ли я двигаться самостоятельно")
                weights_ice = {}
                for eid, weights in ship['weights'][get_weights_period(ship_current_time)].items():
                    weights_ice[str(eid)] = weights['solo']
                path_to_destination_1 = dynamic_weight_shortest_path(G, ship_start, ship_end, weights_ice)

                idx_1 = 1
                point = path_to_destination_1[idx_1]
                prev_point = path_to_destination_1[idx_1 - 1]
                edge_id = G.get_edge_data(prev_point, point)['id']
                solo_weight = ship["weights"][get_weights_period(ship_current_time)][edge_id]["solo"]
                prov_weight = ship["weights"][get_weights_period(ship_current_time)][edge_id]["provided"]
                dprint("Самовольно: " + points[str(prev_point)]['name'] + " " + points[str(point)]['name'] + " " + str(
                    solo_weight))
                clear = float(edges[str(edge_id)]['length']) / ship['speed'] == solo_weight
                if solo_weight != float('inf') and solo_weight != 10000000:
                    unit_time = ship_current_time + timedelta(hours=solo_weight)
                    dprint(unit_time.strftime("%Y-%m-%d %H:%M:%S") + " " + time_for_icebreaker.strftime(
                        "%Y-%m-%d %H:%M:%S"))
                    if unit_time <= time_for_icebreaker or time_to_port >= solo_weight or solo_weight:
                        dprint("Продвинусь на ребро вперед  попробую в следющй раз")
                        ship_current_time += timedelta(hours=solo_weight)
                        ship_routes[ship_name]["route"].append({
                            "port": point,
                            "coords": points[str(point)]["coords"],
                            "port_name": points[str(point)]["name"],
                            "date": unit_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "time": solo_weight,
                            "provided": False,
                            "waiting": False
                        })
                        assigned_icebreakers[ship_name] = None
                        queue.add({
                            "name": ship_name,
                            "start": point,
                            "id": ship['id'],
                            "end": ship_end,
                            "departure_time": unit_time,
                            "current_time": unit_time,
                            "route": ship_route
                        })
                        total_ships_time += solo_weight
                        dprint("Next")
                        continue

                    # if icebreaker:
                if prov_weight == float('inf'):
                    queue.add({
                        "name": ship_name,
                        "start": prev_point,
                        "id": ship['id'],
                        "end": ship_end,
                        "departure_time": ship_departure_time+timedelta(hours=24),
                        "current_time": ship_departure_time+timedelta(hours=24),
                        "route": ship_route
                    })
                    ship_routes[ship_name]["route"].append({
                        "port": prev_point,
                        "coords": points[str(prev_point)]["coords"],
                        "port_name": points[str(prev_point)]["name"],
                        "date": (ship_departure_time+timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"),
                        "time": 24,
                        "provided": False,
                        "waiting": True
                    })
                    total_ships_time += solo_weight
                    dprint("INFINITE_ROUTE")
                    continue
            if icebreaker:
                dprint("Ледокол нашелся - " + icebreaker['name'])
                dprint(total_to_end)
                icebreaker_queue[nearest_port].remove(icebreaker)
                icebreaker = move_icebreaker(icebreaker, nearest_port, ship_start)
                if 'route' not in icebreaker:
                    icebreaker['route'] = [
                        {
                            "port": icebreaker['startPosition'],
                            "coords": points[str(icebreaker['startPosition'])]["coords"],
                            "port_name": points[str(icebreaker['startPosition'])]["name"],
                            "date": icebreaker['startTime'],
                            "time": 0,
                            "convoy": []
                        }
                    ]
                    icebreaker['startTime'] = datetime.strptime(icebreaker['startTime'], "%Y-%m-%d %H:%M:%S")

                icebreaker_start_time = icebreaker['startTime']
                if isinstance(icebreaker_start_time, str):
                    icebreaker_start_time = datetime.strptime(icebreaker['startTime'], "%Y-%m-%d %H:%M:%S")
                icebreaker_time = icebreaker_start_time

                if icebreaker_start_time < ship_departure_time:
                    waiting_time = (ship_departure_time - icebreaker_start_time).total_seconds() / 3600
                    dprint("Ледокол ждет " + str(waiting_time) + " часов (" + icebreaker['name'] + ')',
                           ship_departure_time)
                    total_ice_wait += waiting_time
                    icebreaker['route'].append({
                        "port": ship_start,
                        "coords": points[str(ship_start)]["coords"],
                        "port_name": points[str(ship_start)]["name"],
                        "date": ship_departure_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "time": waiting_time,
                        "convoy": [],
                        "waiting": True
                    })
                    icebreaker['startTime'] = ship_departure_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    waiting_time = (icebreaker_start_time - ship_departure_time).total_seconds() / 3600
                    total_ships_time += waiting_time
                    total_ships_wait += waiting_time
                    ship_routes[ship_name]["route"].append({
                        "port": ship_start,
                        "coords": points[str(ship_start)]["coords"],
                        "port_name": points[str(ship_start)]["name"],
                        "date": icebreaker['startTime'],
                        "time": waiting_time,
                        "provided": False,
                        "waiting": True
                    })
                    dprint("Судно ждет " + str(waiting_time) + " часов", ship_departure_time)
                    ship_departure_time = icebreaker_start_time

                dprint("Начинаю просчитывать совместный маршрут", icebreaker_start_time)
                # path_to_destination = nx.shortest_path(G, source=ship_start, target=ship_end, weight='weight')
                weights_ice = {}
                dprint(get_weights_period(ship_current_time))
                for eid, weights in ship['weights'][get_weights_period(ship_current_time)].items():
                    weights_ice[str(eid)] = weights['provided']
                path_to_destination = dynamic_weight_shortest_path(G, ship_start, ship_end, weights_ice)
                time1 = dynamic_weight_shortest_path_length(G, 8, 47, weights_ice)

                # region Поиски сдуен в караван
                efficient = []
                dprint("Проверяю, могу ли кого-нибудь прхватить по дороге")
                random_bool = random.choice([True, False])
                random_bool = False
                if random_bool:
                    for ship_added in queue:
                        added_from = ship_added['route'][0]
                        added_to = ship_added['route'][1]
                        ship_added_model = ships_data[ship_added['id']]
                        paths = compare_routes(ship_start, ship_end, added_from, added_to,
                                               ship['weights'][get_weights_period(ship_added['departure_time'])],
                                               ship_added_model['weights'][
                                                   get_weights_period(ship_added['departure_time'])])
                        # if len(paths.cross) < 2: continue
                        time_to_meet = find_path_time(paths.path_to, [ship, icebreaker], ship_departure_time)
                        time_to_back = find_path_time(paths.cross, [ship, icebreaker, ship_added_model],
                                                      ship_departure_time)
                        time_clear = find_path_time(paths.clear_path, [ship, icebreaker], ship_departure_time)

                        # if float('inf') in time_to_meet.values(): continue
                        # if float('inf') in time_to_back.values(): continue
                        # if float('inf') in time_clear.values(): continue
                        time_to_wait = max(ship_departure_time + timedelta(hours=max(time_to_meet.values())),
                                           ship_added['departure_time'])
                        time_for_covoy = time_to_wait + timedelta(hours=max(time_to_back.values()))
                        time_clear = ship_departure_time + timedelta(hours=max(time_clear.values()))
                        solo_hours = min(
                            max(find_path_time(paths.cross, [ship_added_model], ship_departure_time, 'solo').values()),
                            50000)
                        time_for_solo = ship_added['departure_time'] + timedelta(hours=solo_hours)
                        dprint([points[str(point_id)]['name'] + " ->" for point_id in paths.path_after])
                        dprint([points[str(point_id)]['name'] + " ->" for point_id in paths.path_to])
                        dprint([points[str(point_id)]['name'] + " ->" for point_id in paths.path_common])
                        dprint([points[str(point_id)]['name'] + " ->" for point_id in paths.second_path])
                        dprint([points[str(point_id)]['name'] + " ->" for point_id in paths.cross])
                        dprint("Время до встречи: " + str(time_to_meet) + " время на возврат: " + str(
                            time_to_back) + " чистое время: " + str(time_clear) + " " + ship_added['name'])
                        dprint("Время с заездом: " + str(time_for_covoy) + " время без заезда: " + str(
                            time_clear) + " самостоятельно: " + str(time_for_solo) + " " + ship_added['name'])
                        # HOURS_FOR_WAIT = coeffs[ship['id']]
                        HOURS_FOR_WAIT = hours_to_wait
                        if (
                                time_for_covoy - time_clear).total_seconds() / 3600 < HOURS_FOR_WAIT and time_for_solo > time_for_covoy:
                            dprint("!!!!!   Халява, надо забрать с собой " + ship_added['name'] + " до " +
                                   points[str(paths.cross[-1])]['name'])
                            wait_for_ship = 0 if ship_departure_time + timedelta(hours=max(time_to_meet.values())) < \
                                                 ship_added[
                                                     'departure_time'] else (ship_departure_time + timedelta(
                                hours=max(time_to_meet.values())) -
                                                                             ship_added[
                                                                                 'departure_time']).total_seconds() / 3600
                            wait_for_icebreaker = 0 if ship_departure_time + timedelta(
                                hours=max(time_to_meet.values())) > \
                                                       ship_added['departure_time'] else (ship_added[
                                                                                              'departure_time'] - (
                                                                                                  ship_departure_time + timedelta(
                                                                                              hours=max(
                                                                                                  time_to_meet.values())))).total_seconds() / 3600
                            efficient.append(
                                {"name": ship_added['name'],
                                 "to": points[str(paths.cross[-1])]['name'],
                                 "loses": (time_for_covoy - time_clear).total_seconds() / 3600,
                                 "route_to": [points[str(point_id)]['name'] + " ->" for point_id in paths.path_to],
                                 "cross": [points[str(point_id)]['name'] + " ->" for point_id in paths.cross],
                                 "waiting_time_icebreaker": wait_for_icebreaker,
                                 "waiting_time_ship": wait_for_ship,
                                 "route": paths.cross,
                                 "ship_model": ship_added_model,
                                 "ship": ship_added,
                                 'full_path': paths.path_common
                                 })

                # print(efficient)
                # json.dumps(efficient)

                added_edges = {}
                wait = []
                if len(efficient) > 1:
                    print([test['loses'] for test in efficient])
                if (len(efficient)):
                    ship_new = min(efficient, key=itemgetter('loses'))
                    ship_new = efficient[random.randint(0, len(efficient) - 1)]
                    # if (ship_new['name'] == "NIKOLAY YEVGENOV"):
                    #     print(ship_new)
                    wait.append({'id': ship_new['route'][0], 'time': ship_new['waiting_time_icebreaker']})
                    path_to_destination = ship_new['full_path']
                    ship_new_time = ship_new['ship']['departure_time']
                    # ship_requests.remove(ship_new)
                    if (ship_new['waiting_time_ship'] > 0):
                        ship_new_time += timedelta(hours=ship_new['waiting_time_ship'] + 0.1)
                        ship_routes[ship_new['name']]["route"].append({
                            "port": ship_new['ship_model']['route'][0],
                            "coords": points[str(ship_new['ship_model']['route'][0])]["coords"],
                            "port_name": points[str(ship_new['ship_model']['route'][0])]["name"],
                            "date": ship_new_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "time": ship_new['waiting_time_ship'] + 0.1,
                            "provided": False,
                            "waiting": True,
                            "test": True
                        })
                    for idx, port in enumerate(ship_new['route']):
                        if idx == 0: continue
                        prev = ship_new['route'][idx - 1]
                        times = find_path_time([prev, port], [icebreaker, ship, ship_new['ship_model']], ship_new_time)
                        edge_time = max(times.values())
                        ship_new_time += timedelta(hours=edge_time)
                        added_edges[G.get_edge_data(prev, port)['id']] = {'time': edge_time,
                                                                          'ships': [ship_new['name']],
                                                                          'from': prev, 'to': port}
                        total_ships_time += edge_time
                        ship_routes[ship_new['name']]["route"].append({
                            "port": port,
                            "coords": points[str(port)]["coords"],
                            "port_name": points[str(port)]["name"],
                            "date": ship_new_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "time": edge_time,
                            "provided": True,
                            "waiting": False
                        })
                    ship_requests.appendleft({
                        "name": ship_new['name'],
                        "start": port,
                        "id": ship_new['ship_model']['id'],
                        "end": ship_new['ship_model']['route'][1],
                        "departure_time": ship_new_time,
                        "current_time": ship_new_time,
                        "route": ship_new['ship_model']['route']
                    })
                    queue.add({
                        "name": ship_new['name'],
                        "start": port,
                        "id": ship_new['ship_model']['id'],
                        "end": ship_new['ship_model']['route'][1],
                        "departure_time": ship_new_time,
                        "current_time": ship_new_time,
                        "route": ship_new['ship_model']['route']
                    })
                met = False
                ### endregion

                icebreaker_point = False
                dprint([points[str(pt)]['name'] for pt in path_to_destination])
                dprint([str(pt) for pt in path_to_destination])
                cont = False
                for idx, point in enumerate(path_to_destination):
                    ship_current_time = max(ship_current_time, icebreaker_start_time)
                    if idx == 0:
                        continue
                    prev_point = path_to_destination[idx - 1]

                    if (len(wait) > 0):
                        if (prev_point == wait[0]['id']):
                            ship_current_time += timedelta(hours=wait[0]['time'])

                            icebreaker['route'].append({
                                "port": prev_point,
                                "coords": points[str(prev_point)]["coords"],
                                "port_name": points[str(prev_point)]["name"],
                                "date": ship_current_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "time": wait[0]['time'],
                                "convoy": [ship_name],
                                "waiting": True
                            })
                            icebreaker['startTime'] = ship_departure_time.strftime("%Y-%m-%d %H:%M:%S")
                            total_ships_time += waiting_time
                            total_ships_wait += waiting_time
                            ship_routes[ship_name]["route"].append({
                                "port": prev_point,
                                "coords": points[str(prev_point)]["coords"],
                                "port_name": points[str(prev_point)]["name"],
                                "date": ship_current_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "time": wait[0]['time'],
                                "provided": True,
                                "waiting": True
                            })

                    edge_id = G.get_edge_data(prev_point, path_to_destination[idx])['id']
                    # print(edge_id)
                    st = get_weights_period(ship_current_time)
                    ship_solo_weight = ship["weights"][get_weights_period(ship_current_time)][edge_id]["solo"]
                    ship_provided_weight = ship["weights"][get_weights_period(ship_current_time)][edge_id]["provided"]
                    icebreaker_provided_weight = icebreaker["weights"][get_weights_period(ship_current_time)][edge_id][
                        "solo"]
                    dprint((ship_provided_weight, icebreaker_provided_weight))
                    travel_time = max(ship_provided_weight, icebreaker_provided_weight)
                    extended_convoy = []
                    if (met):
                        if len(added_edges) > 0:
                            if added_edges[edge_id]['to'] == path_to_destination[idx] and added_edges[edge_id][
                                'from'] == prev_point:
                                extended_convoy = added_edges[edge_id]['ships']
                                travel_time = max(travel_time, added_edges[edge_id]['time'])
                                added_edges.pop(edge_id)
                    dprint(str(prev_point) + " " + str(edge_id) + " " + str(travel_time), ship_current_time)
                    if len(wait) > 0 and point == wait[0]['id']:
                        met = True

                    elif travel_time == float('inf'):
                        cont = True
                        dprint("Встряли вместе")
                        break
                    if ship_solo_weight > travel_time:
                        ship_current_time += timedelta(hours=travel_time)
                        ship_routes[ship_name]["route"].append({
                            "port": point,
                            "coords": points[str(point)]["coords"],
                            "port_name": points[str(point)]["name"],
                            "date": ship_current_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "time": travel_time,
                            "provided": True,
                            "waiting": False
                        })
                        dprint("Фикссирую ледокол в точке " + points[str(point)]["name"], ship_current_time)
                        icebreaker['route'].append({
                            "port": point,
                            "coords": points[str(point)]["coords"],
                            "port_name": points[str(point)]["name"],
                            "date": ship_current_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "time": travel_time,
                            "convoy": [ship_name] + extended_convoy
                        })
                        icebreaker_time = ship_current_time
                        icebreaker_point = point


                    else:
                        ship_current_time += timedelta(hours=ship_solo_weight)
                        ship_routes[ship_name]["route"].append({
                            "port": point,
                            "coords": points[str(point)]["coords"],
                            "port_name": points[str(point)]["name"],
                            "date": ship_current_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "time": ship_solo_weight,
                            "provided": False,
                            "waiting": False
                        })
                        break

                # region Если встряли на маршруте
                if cont:
                    dprint("", icebreaker_time)
                    dprint("", ship_current_time)
                    dprint(points[str(prev_point)]['name'], ship_current_time)
                    icebreaker['startTime'] = ship_current_time.strftime("%Y-%m-%d %H:%M:%S")
                    ship_current_time += timedelta(days=1)
                    ship_current_time += timedelta(days=1)
                    ship_routes[ship_name]["route"].append({
                        "port": prev_point,
                        "coords": points[str(prev_point)]["coords"],
                        "port_name": points[str(prev_point)]["name"],
                        "date": ship_current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "time": 24,
                        "provided": False,
                        "waiting": True
                    })
                    queue.add({
                        "name": ship_name,
                        "start": prev_point,
                        "id": ship['id'],
                        "end": ship_end,
                        "departure_time": request['departure_time'] + timedelta(days=1),
                        "current_time": request['current_time'] + timedelta(days=1),
                        "route": ship_route
                    })
                    icebreaker_queue[prev_point].append(icebreaker)
                    continue
                # endregion

                dprint("Начинаю просчитывать самостоятельный маршрут", ship_current_time)
                prev_point = path_to_destination[idx - 1]
                dprint(str(idx) + " " + str(len(path_to_destination)) + " " + points[str(prev_point)]['name'] + " " +
                       points[str(path_to_destination[idx])]['name'])
                if (idx == len(path_to_destination)):
                    prev_point = path_to_destination[idx]
                if (icebreaker_point):
                    prev_point = icebreaker_point
                icebreaker['startPosition'] = prev_point
                dprint("Закончил в " + points[str(prev_point)]["name"], icebreaker_time)
                icebreaker['startTime'] = icebreaker_time.strftime("%Y-%m-%d %H:%M:%S")
                icebreaker['startTimestamp'] = datetime.strptime(icebreaker['startTime'], "%Y-%m-%d %H:%M:%S")
                dprint(icebreaker['startTime'])
                if prev_point not in icebreaker_queue:
                    icebreaker_queue[prev_point] = deque()
                icebreaker_queue[prev_point].append(icebreaker)
                icebreaker_routes.append({
                    "name": icebreaker['name'],
                    "id": "ice" + str(icebreaker['id']),
                    "type": "ice",
                    "ice_class": icebreaker['iceClass'],
                    "route": icebreaker['route']
                })

                while idx < len(path_to_destination) - 1:
                    idx += 1
                    point = path_to_destination[idx]
                    prev_point = path_to_destination[idx - 1]
                    edge_id = G.get_edge_data(prev_point, point)['id']
                    dprint("Самостоятельно: " + points[str(prev_point)]['name'] + " " + points[str(point)]['name'])
                    solo_weight = ship["weights"][get_weights_period(ship_current_time)][edge_id]["solo"]

                    if solo_weight > 100:
                        dprint("Не, торможу: " + points[str(prev_point)]['name'] + " " + points[str(point)]['name'])
                        assigned_icebreakers[ship_name] = None
                        ship_requests.appendleft({
                            "name": ship_name,
                            "start": prev_point,
                            "id": ship['id'],
                            "end": ship_end,
                            "departure_time": ship_current_time,
                            "current_time": ship_current_time,
                            "route": ship_route
                        })
                        queue.add({
                            "name": ship_name,
                            "start": prev_point,
                            "id": ship['id'],
                            "end": ship_end,
                            "departure_time": ship_current_time,
                            "current_time": ship_current_time,
                            "route": ship_route
                        })
                        break

                    ship_current_time += timedelta(hours=solo_weight)
                    ship_routes[ship_name]["route"].append({
                        "port": point,
                        "coords": points[str(point)]["coords"],
                        "port_name": points[str(point)]["name"],
                        "date": ship_current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "time": solo_weight,
                        "provided": False,
                        "waiting": False
                    })

                dprint("Цикл завершен")
            else:

                print(ship_name)
                print("!!!!!!!!!!!!!!!!!!!!!")
                request['departure_time'] += timedelta(days=1)
                request['current_time'] += timedelta(days=1)
                ship_routes[ship_name]["route"].append({
                    "port": ship_start,
                    "coords": points[str(ship_start)]["coords"],
                    "port_name": points[str(ship_start)]["name"],
                    "date": request['current_time'].strftime("%Y-%m-%d %H:%M:%S"),
                    "time": 24,
                    "provided": False,
                    "waiting": True
                })
                print(request)
                if (request['current_time'] > datetime.strptime("2022-06-13 00:00:00", "%Y-%m-%d %H:%M:%S")):
                    print("Невозможно доатсвить судно")
                else:
                    queue.add(request)
                # sleep(1)

        # Объединяем маршруты судов и ледоколов в один массив
        all_routes = [{

            "name": icebreaker['name'],
            "id": "ice" + str(icebreaker['id']),
            "type": "ice",
            "ice_class": icebreaker['iceClass'],
            "date": ice_times[icebreaker['id']],
            "route": icebreaker['route']
        } for icebreaker in icebreakers_data] + list(ship_routes.values())

        print('_____________________________________________________________________________')
        print(hours_to_wait)
        test_all_time = 0
        for route in ship_routes.values():
            test_all_time += (datetime.strptime(route['route'][-1]['date'], "%Y-%m-%d %H:%M:%S") - datetime.strptime(
                route['route'][0]['date'], "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600
            # print(route['name']+" "+str((datetime.strptime(route['route'][-1]['date'], "%Y-%m-%d %H:%M:%S") - datetime.strptime(
            #     route['route'][0]['date'], "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600))

        wait_all = 0
        for route in ship_routes.values():
            for point in route['route']:
                # print(point)
                if point['waiting']:
                    wait_all += point['time']
        print(str(hours_to_wait) + " " + str(test_all_time))
        all_times.append(test_all_time)
        min_common_time = min(min_common_time, test_all_time)
        if (test_all_time <= min_common_time):
            min_common_time = test_all_time
            min_routes = all_routes
            min_i = hours_to_wait

    print(min_common_time)
    print(min_i)
    print(set(all_times))
    # Запись маршрутов в файлы
    # with open('icebreaker_routes.json', 'w', encoding='utf-8') as f:
    #     json.dump(icebreaker_routes, f, ensure_ascii=False, indent=4)
    #
    # with open('ship_routes.json', 'w', encoding='utf-8') as f:
    #     json.dump(list(ship_routes.values()), f, ensure_ascii=False, indent=4)

    with open('static/json/ships_all.json', 'w', encoding='utf-8') as f:
        json.dump(min_routes, f, ensure_ascii=False, indent=4)

    # Загрузка данных для диаграммы Ганта
    with open('static/json/ships_all.json', 'r', encoding='utf-8') as f:
        all_routes = json.load(f)

    print("Total ships time " + str(total_ships_time))
    print("Total ships wait " + str(total_ships_wait))
    print("Total ice wait " + str(total_ice_wait))

    # Функция для создания диаграммы Ганта
    def create_gantt_chart(routes):
        fig, ax = plt.subplots(figsize=(15, 10))

        colors = {
            'ship': 'skyblue',
            'ice': 'coral',
            'provided': 'lightgreen'
        }

        for idx, route in enumerate(routes):
            name = route['name']
            route_type = route['type']
            start_time = datetime.strptime(route['date'], "%Y-%m-%d %H:%M:%S")

            for segment in route['route']:
                duration = timedelta(hours=segment['time'])
                end_time = start_time + duration
                # print(segment, route_type)
                if segment.get('waiting', False):
                    bar_color = 'grey'
                    ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black', hatch='/')
                elif segment.get('convoy') or segment.get('provided'):
                    bar_color = 'lightgreen'
                    ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black')
                else:
                    if route_type == "ship":
                        bar_color = 'lightblue'
                        ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black')
                    else:
                        bar_color = 'coral'
                        ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black')

                start_time = datetime.strptime(segment['date'], "%Y-%m-%d %H:%M:%S")

        # Настройка осей
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        ax.set_xlabel('Time')
        ax.set_ylabel('Ships and Icebreakers')
        ax.set_title('Gantt Chart of Ship and Icebreaker Routes')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Добавление легенды
        legend_elements = [
            plt.Line2D([0], [0], color='skyblue', lw=4, label='Корабль'),
            plt.Line2D([0], [0], color='coral', lw=4, label='Ледокол'),
            plt.Line2D([0], [0], color='lightgreen', lw=4, label='Проводка'),
            plt.Line2D([0], [0], color='grey', lw=4, label='Ожидание', linestyle='dashed')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        plt.savefig('static/gant.png')
        print('saved')
        with PdfPages('static/gant_individual.pdf') as pdf:
            for route in routes:
                name = route['name']
                route_type = route['type']

                start_time = datetime.strptime(route['date'], "%Y-%m-%d %H:%M:%S")

                fig, ax = plt.subplots(figsize=(15, 5))
                for segment in route['route']:
                    duration = timedelta(hours=segment['time'])
                    end_time = start_time + duration

                    if segment.get('waiting', False):
                        bar_color = 'grey'
                        ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black', hatch='/')
                    elif segment.get('convoy') or segment.get('provided'):
                        bar_color = 'lightgreen'
                        if segment.get('convoy'):
                            if len(segment.get('convoy')) > 1:
                                ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black',
                                        hatch='/')
                            else:
                                ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black')
                        else:
                            ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black')
                    else:
                        if route_type == "ship":
                            bar_color = 'skyblue'
                            ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black')
                        else:
                            bar_color = 'coral'
                            ax.barh(y=name, left=start_time, width=duration, color=bar_color, edgecolor='black')

                    # костыль
                    start_time = start_time + duration

                # Настройка осей для диаграммы конкретного корабля
                ax.xaxis_date()
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
                ax.set_xlabel('Время')
                ax.set_ylabel(name)
                ax.set_title(f'Диаграмма Ганта для {name}')
                plt.xticks(rotation=45)
                plt.tight_layout()

                # Добавление легенды для диаграммы конкретного корабля
                ax.legend(handles=legend_elements, loc='upper right')

                # Сохранение диаграммы конкретного корабля в PDF
                pdf.savefig(fig)
                plt.close(fig)

        plt.close('all')

    # Создание диаграммы Ганта
    create_gantt_chart(all_routes)

if __name__ == '__main__':
    solve_schedules()