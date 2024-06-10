import json

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import locale
from datetime import datetime


# Файл для первичного обсчета графа в разрезе ледовых классов (см. map.json)


from numpy import Inf, Infinity
import pandas as pd
from math import sqrt


DEBUG = False
IntegrValues = {}

import time


def time_of_function(function):
    def wrapped(*args):
        start_time = time.perf_counter_ns()
        res = function(*args)
        print(f"Время выполнения {function.__name__}:", time.perf_counter_ns() - start_time)
        return res

    return wrapped


# Определяем координаты сектора, в котором находится точка.
def get_dots_sector(dot):
    # Получаем значения широты и долготы
    dot_y = dot[0]
    dot_x = dot[1]
    min_distance = Infinity
    min_distance_sector_x = Infinity
    min_distance_sector_y = Infinity

    for sector_y, sector_x in IntegrValues:
        # Ограничения для оптимизации перебора.
        if sector_x > dot_x or sector_y < dot_y:
            continue  # если точка не слева сверху
        # if dot_x - sector_x > 1 or sector_y - dot_y > 1:
        #     continue  # если точка более чем в 5 градусах

        if dot_x - sector_x + sector_y - dot_y < min_distance:
            min_distance = dot_x - sector_x + sector_y - dot_y
            min_distance_sector_x = sector_x
            min_distance_sector_y = sector_y

        # Возвраащаем значения широты и долготы
    return min_distance_sector_y, min_distance_sector_x


def parse_velocity(velocity: int):
    # print(velocity)
    speed_zero = 0
    bool = False
    if velocity >= 19.5:
        type = 'light'
    elif velocity >= 14.5:
        type = 'medium'
    elif velocity >= 9.5:
        type = 'hard'
    else:
        type = 'light'
        # bool = True

    LIMITS = {
        'Arc7': {
            'provided': {
                'medium': 0.8,
                'hard': 0.8,
                'light': 1
            },
            'solo': {
                'medium': 0.6,
                'hard': 0.15,
                'light': 1
            }
        },
        'Arc4': {
            'provided': {
                'medium': 0.8,
                'hard': 0.7,
                'light': 1
            },
            'solo': {
                'medium': speed_zero,
                'hard': speed_zero,
                'light': 1
            }
        },
        'Arc5': {
            'provided': {
                'medium': 0.8,
                'hard': 0.7,
                'light': 1
            },
            'solo': {
                'medium': speed_zero,
                'hard': speed_zero,
                'light': 1
            }
        },
        'Arc6': {
            'provided': {
                'medium': 0.8,
                'hard': 0.7,
                'light': 1
            },
            'solo': {
                'medium': speed_zero,
                'hard': speed_zero,
                'light': 1
            }
        },
        'нет': {
            'provided': {
                'medium': 1,
                'hard': 1,
                'light': 1
            },
            'solo': {
                'medium': speed_zero,
                'hard': speed_zero,
                'light': 1
            }
        }
    }
    case = {}
    for ice_class, value in LIMITS.items():
        case[ice_class] = {
            'solo': type if bool else value['solo'][type],
            'provided': type if bool else value['provided'][type],
        }
    return case




# Считаем длину всей прямой
def get_total_line_time_coefficient(a, b, line_length):
    # a.reverse()
    # b.reverse()

    if a[0] < b[0]:  # Убеждаемся, что первая точка левее второй.
        a, b = b, a

    # print(a, b)
    amount_of_pieces = 100
    if DEBUG: print("Количество кусочков: ", amount_of_pieces)
    piece_length = line_length / amount_of_pieces
    if DEBUG: print("Длина кусочков: ", piece_length)
    total_line_time = 0
    lines = {}
    for i in range(amount_of_pieces):
        lattitude = a[0] + i * (b[0] - a[0]) / amount_of_pieces
        longitude = a[1] + i * (b[1] - a[1]) / amount_of_pieces
        if DEBUG: print(f"{i} Точка: {lattitude}, {longitude}")
        lattitude, longitude = get_dots_sector((lattitude, longitude))
        if DEBUG: print(f"{i} Сектор: {lattitude}, {longitude}")
        tmp = parse_velocity(IntegrValues[(lattitude, longitude)])
        for ice_class, data in tmp.items():
            if lines.get(ice_class):
                if lines[ice_class]['solo'].get(data['solo']):
                    lines[ice_class]['solo'][data['solo']] += piece_length
                else:
                    lines[ice_class]['solo'][data['solo']] = piece_length
                if lines[ice_class]['provided'].get(data['provided']):
                    lines[ice_class]['provided'][data['provided']] += piece_length
                else:
                    lines[ice_class]['provided'][data['provided']] = piece_length
            else:
                lines[ice_class] = {'solo': {data['solo']: piece_length}, 'provided': {data['provided']: piece_length}}
    # print(lines)

    for ice_class, data in lines.items():
        for type, value in data.items():
            speed_koeff = 0
            for speed, length in value.items():
                speed_koeff += length/speed
            lines[ice_class][type] = speed_koeff


    return lines


if __name__ == "__main__":
    file_path = "/data/IntegrVelocity.xlsx"
    xls = pd.ExcelFile(file_path)

    lat = pd.read_excel(xls, "lat")
    lon = pd.read_excel(xls, "lon")
    first_week = pd.read_excel(xls, "03-Mar-2020")

    # Определяем максимальное количество строк и столбцов из обоих листов
    max_rows = max(lat.shape[0], lon.shape[0], first_week.shape[0])
    max_cols = max(lat.shape[1], lon.shape[1], first_week.shape[1])

    # Проходим по каждой координате одновременно
    for i in range(max_rows):
        for j in range(max_cols):
            lat_value = lat.iat[i, j] if i < lat.shape[0] and j < lat.shape[1] else None
            lon_value = lon.iat[i, j] if i < lon.shape[0] and j < lon.shape[1] else None
            first_week_value = first_week.iat[i, j] if i < first_week.shape[0] and j < first_week.shape[1] else None
            IntegrValues[(lat_value, lon_value)] = first_week_value


    file_path_graph = 'data/1ГрафДанные.xlsx'
    points_df = pd.read_excel(file_path_graph, sheet_name='points')
    edges_df = pd.read_excel(file_path_graph, sheet_name='edges')

    port_name_to_id = {row['point_name']: row['point_id'] for _, row in points_df.iterrows()}
    port_name_to_coords = {row['point_name']: [row['latitude'], row['longitude']] for _, row in points_df.iterrows()}
    port_id_to_coords = {row['point_id']: [row['latitude'], row['longitude']] for _, row in points_df.iterrows()}


    map = {}
    for i, row in edges_df.iterrows():
        print(f"{i} Ребро: {i}")
        map[int(row['id'])] = get_total_line_time_coefficient(port_id_to_coords[row['start_point_id']], port_id_to_coords[row['end_point_id']], row['length'])
        # if i == 5: break
    # print(map)
    json_file_path = "map.json"
    with open(json_file_path, 'w') as json_file:
        json.dump(map, json_file, indent=4, ensure_ascii=False)
