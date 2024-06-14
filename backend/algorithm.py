import heapq
import json
import sys
from time import sleep

import networkx as nx
from datetime import datetime, timedelta
from collections import deque

from matplotlib import pyplot as plt
import matplotlib.dates as mdates


#работает для проводки судов но с дурацким преследованием самостоятельных

HOURS_FOR_WAIT = 36

# Загрузка данных
def load_json_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

edges = load_json_data('test/edges.json')
icebreakers_data = load_json_data('test/icebreakers.json')
points = load_json_data('test/points_upd.json')
ships_data = load_json_data('test/ships.json')
DEBUG = False
sleep_timeout = 1
if len(sys.argv) > 1:
    DEBUG = True

if len(sys.argv) > 2:
    sleep_timeout = int(sys.argv[2])


def dprint(string, time = False):
    if(DEBUG):
        if time:
            print(time.strftime("%Y-%m-%d %H:%M:%S")+" - "+str(string))
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

# Инициализация всех возможных портов в icebreaker_queue
all_ports = set()
for edge in edges.values():
    point1, point2 = edge['points']
    all_ports.add(point1)
    all_ports.add(point2)

icebreaker_queue = {port: deque() for port in all_ports}

# Добавляем ледоколы в их начальные позиции в очереди
for icebreaker in icebreakers_data:
    if ' ' not in icebreaker['startTime']:
        icebreaker['startTime'] += " 00:00:00"
    icebreaker_queue[icebreaker['startPosition']].append(icebreaker)
    ice_times[icebreaker['id']] = icebreaker['startTime']

# Инициализация маршрутов ледоколов и судов
icebreaker_routes = []
ship_routes = {ship['name']: {
    "name": ship['name'],
    "type": "ship",
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
} for ship in ships_data}

# Добавление всех судов в очередь заявок
for ship in ships_data:
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
assigned_icebreakers = {ship['name']: None for ship in ships_data}

ships_data = {x['id']: x for x in ships_data}

def compare_routes(start, end, second_start, second_end):
    second_path = nx.shortest_path(G, source=second_start, target=second_end, weight='weight')
    path_common, path_to, path_after = find_paththrough(start, end, second_start)
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
        i+=1
    if len(cross) > 1:
        clear_path = nx.shortest_path(G, source=start, target=cross[-1])
    else:
        clear_path = []

    class ComplexPath:
        def __init__(self, path_common, path_to, path_after, second_path, cross, clear_path):
            self.path_common = path_common # цельный общий маршрут
            self.path_after = path_after # путь каравана после встречи
            self.cross = cross # общий путь в караване
            self.second_path = second_path # полный путь второго
            self.path_to = path_to # путь до места встречи
            self.clear_path = clear_path # путь ледокола в чистую, ьез захода

    return ComplexPath(path_common, path_to, path_after, second_path, cross, clear_path)
def find_paththrough(start_location, end_location, through_location):
    path_to_through = nx.shortest_path(G, source=start_location, target=through_location, weight='weight')
    pathh_to_end = nx.shortest_path(G, source=through_location, target=end_location, weight='weight')
    return path_to_through+pathh_to_end[1:], path_to_through, pathh_to_end



def find_path_time(path, ships, key="provided"):
    times = {}
    for ship in ships:
        times[ship["id"]] = 0
        for id, edge in enumerate(path):
            if id == 0: continue
            edge_id  = G.get_edge_data(path[id], path[id-1])['id']

            times[ship["id"]]+=ship['weights'][str(edge_id)][key]
    return times
# print(ships_data[8])
# test = compare_routes(11,18, 25, 16)
# print(find_path_time(test[4], [ships_data[0]]))
# print(compare_routes(11,18, 25, 16))
# exit()

def find_nearest_icebreaker(port, icebreaker_queue):
    """
    Находит ближайший ледокол к указанному порту.
    """
    min_distance = datetime.max
    nearest_icebreaker = None
    nearest_port = None

    for start_port, queue in icebreaker_queue.items():
        if queue:
            path_to_destination = nx.shortest_path(G, source=start_port, target=port, weight='weight')
            time_to_port = 0
            for destination in path_to_destination:
                time_to_port+=queue[0]['weights'][str(destination)]['solo']
            distance = datetime.strptime(queue[0]['startTime'], "%Y-%m-%d %H:%M:%S") + timedelta(hours=time_to_port)
            dprint(queue[0]['name']+" "+points[str(start_port)]['name']+" "+distance.strftime("%Y-%m-%d %H:%M:%S"))
            if distance < min_distance:
                min_distance = distance
                nearest_icebreaker = queue[0]
                nearest_port = start_port

    return nearest_icebreaker, nearest_port, min_distance, time_to_port

# Перемещаем ледокол от начальной точки до конечной, обновляя маршрут и время
def move_icebreaker(icebreaker, start, end):
    """
    Перемещает ледокол от начальной точки до конечной, обновляя маршрут и время.
    """
    path = nx.shortest_path(G, source=start, target=end, weight='weight')
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
        icebreaker_edge_weight = icebreaker["weights"][str(edge_id)]["solo"]
        icebreaker_start_time += timedelta(hours=icebreaker_edge_weight)
        dprint("Первое перемещение "+points[str(prev_point)]['name']+" - "+points[str(point)]['name'], icebreaker_start_time)

        icebreaker['route'].append({
            "port": point,
            "coords": points[str(point)]["coords"],
            "port_name": points[str(point)]["name"],
            "date": icebreaker_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "time": icebreaker_edge_weight,
            "convoy": []
        })
    icebreaker['startPosition'] = end
    icebreaker['startTime'] = icebreaker_start_time.strftime("%Y-%m-%d %H:%M:%S")
    return icebreaker


# print(ship_requests)

min_common_time = float('inf')


for i in range(0, 72, 1):
    while ship_requests:
        request = ship_requests.popleft()
        ship = ships_data[request['id']]
        ship_name = request['name']
        ship_start = request['start']
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
            icebreaker, nearest_port, time_for_icebreaker, time_to_port = find_nearest_icebreaker(ship_start,
                                                                                                  icebreaker_queue)
            dprint("Пытаюсь понять, могу ли я двигаться самостоятельно")
            path_to_destination_1 = nx.shortest_path(G, source=ship_start, target=ship_end, weight='weight')
            idx_1 = 1
            point = path_to_destination_1[idx_1]
            prev_point = path_to_destination_1[idx_1 - 1]
            edge_id = G.get_edge_data(prev_point, point)['id']
            dprint("Самовольно: " + points[str(prev_point)]['name'] + " " + points[str(point)]['name'])
            solo_weight = ship["weights"][str(edge_id)]["solo"]
            unit_time = ship_current_time + timedelta(hours=solo_weight)
            dprint(unit_time.strftime("%Y-%m-%d %H:%M:%S") + " " + time_for_icebreaker.strftime("%Y-%m-%d %H:%M:%S"))
            if unit_time <= time_for_icebreaker or time_to_port >= solo_weight:
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
                ship_requests.appendleft({
                    "name": ship_name,
                    "start": point,
                    "id": ship['id'],
                    "end": ship_end,
                    "departure_time": unit_time,
                    "current_time": unit_time,
                    "route": ship_route
                })
                continue
            if icebreaker:
                dprint("Ледокол нашелся - " + icebreaker['name'])
                icebreaker_queue[nearest_port].remove(icebreaker)
                icebreaker = move_icebreaker(icebreaker, nearest_port, ship_start)

        if icebreaker:

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

            if icebreaker_start_time < ship_departure_time:
                waiting_time = (ship_departure_time - icebreaker_start_time).total_seconds() / 3600
                dprint("Ледокол ждет " + str(waiting_time) + " часов", ship_departure_time)
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
            path_to_destination = nx.shortest_path(G, source=ship_start, target=ship_end, weight='weight')

            # region Поиски сдуен в караван
            efficient = []
            dprint("Проверяю, могу ли кого-нибудь прхватить по дороге")
            for ship_added in ship_requests:
                added_from = ship_added['route'][0]
                added_to = ship_added['route'][1]
                ship_added_model = ships_data[ship_added['id']]
                paths = compare_routes(ship_start, ship_end, added_from, added_to)
                # if len(paths.cross) < 2: continue
                time_to_meet = find_path_time(paths.path_to, [ship, icebreaker])
                time_to_back = find_path_time(paths.cross, [ship, icebreaker, ship_added_model])
                time_clear = find_path_time(paths.clear_path, [ship, icebreaker])
                time_to_wait = max(ship_departure_time + timedelta(hours=max(time_to_meet.values())),
                                   ship_added['departure_time'])
                time_for_covoy = time_to_wait + timedelta(hours=max(time_to_back.values()))
                time_clear = ship_departure_time + timedelta(hours=max(time_clear.values()))
                solo_hours = min(max(find_path_time(paths.cross, [ship_added_model], 'solo').values()), 50000)
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
                if (
                        time_for_covoy - time_clear).total_seconds() / 3600 < HOURS_FOR_WAIT and time_for_solo > time_for_covoy:
                    dprint("!!!!!   Халява, надо забрать с собой " + ship_added['name'] + " до " +
                           points[str(paths.cross[-1])]['name'])
                    wait_for_ship = 0 if ship_departure_time + timedelta(hours=max(time_to_meet.values())) < ship_added[
                        'departure_time'] else (ship_departure_time + timedelta(hours=max(time_to_meet.values())) -
                                                ship_added['departure_time']).total_seconds() / 3600
                    wait_for_icebreaker = 0 if ship_departure_time + timedelta(hours=max(time_to_meet.values())) > \
                                               ship_added['departure_time'] else (ship_added['departure_time'] - (
                                ship_departure_time + timedelta(
                            hours=max(time_to_meet.values())))).total_seconds() / 3600
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
            if (len(efficient)):
                ship_new = efficient[0]
                # if (ship_new['name'] == "NIKOLAY YEVGENOV"):
                #     print(ship_new)
                wait.append({'id': ship_new['route'][0], 'time': ship_new['waiting_time_icebreaker']})
                path_to_destination = ship_new['full_path']
                ship_new_time = ship_new['ship']['departure_time']
                ship_requests.remove(ship_new['ship'])
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
                    times = find_path_time([prev, port], [icebreaker, ship, ship_new['ship_model']])
                    edge_time = max(times.values())
                    ship_new_time += timedelta(hours=edge_time)
                    added_edges[G.get_edge_data(prev, port)['id']] = {'time': edge_time, 'ships': [ship_new['name']],
                                                                      'from': prev, 'to': port}
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
            met = False
            ### endregion

            icebreaker_point = False
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
                ship_solo_weight = ship["weights"][str(edge_id)]["solo"]
                ship_provided_weight = ship["weights"][str(edge_id)]["provided"]
                icebreaker_provided_weight = icebreaker["weights"][str(edge_id)]["solo"]
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

                total_ships_time += travel_time

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
                    dprint("Ледокол открепился", ship_current_time)
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
            dprint(icebreaker['startTime'])
            if prev_point not in icebreaker_queue:
                icebreaker_queue[prev_point] = deque()
            icebreaker_queue[prev_point].append(icebreaker)
            icebreaker_routes.append({
                "name": icebreaker['name'],
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
                solo_weight = ship["weights"][str(edge_id)]["solo"]

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

            ship_requests.appendleft(request)
            sleep(1)

    # Объединяем маршруты судов и ледоколов в один массив
    all_routes = [{

        "name": icebreaker['name'],
        "type": "ice",
        "ice_class": icebreaker['iceClass'],
        "date": ice_times[icebreaker['id']],
        "route": icebreaker['route']
    } for icebreaker in icebreakers_data] + list(ship_routes.values())

    test_all_time = 0
    for route in ship_routes.values():
        test_all_time += (datetime.strptime(route['route'][-1]['date'], "%Y-%m-%d %H:%M:%S") - datetime.strptime(
            route['route'][0]['date'], "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600

    wait_all = 0
    for route in ship_routes.values():
        for point in route['route']:
            if point['waiting']:
                wait_all += point['time']

    min_common_time = min(min_common_time, test_all_time)
print(min_common_time)
print(wait_all)
# Запись маршрутов в файлы
with open('icebreaker_routes.json', 'w', encoding='utf-8') as f:
    json.dump(icebreaker_routes, f, ensure_ascii=False, indent=4)

with open('ship_routes.json', 'w', encoding='utf-8') as f:
    json.dump(list(ship_routes.values()), f, ensure_ascii=False, indent=4)

with open('ships_all.json', 'w', encoding='utf-8') as f:
    json.dump(all_routes, f, ensure_ascii=False, indent=4)

# Загрузка данных для диаграммы Ганта
with open('ships_all.json', 'r', encoding='utf-8') as f:
    all_routes = json.load(f)


print("Total ships time "+str(total_ships_time))
print("Total ships wait "+str(total_ships_wait))
print("Total ice wait "+str(total_ice_wait))

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
    plt.savefig('gant.png')

    # plt.show()


# Создание диаграммы Ганта
create_gantt_chart(all_routes)
