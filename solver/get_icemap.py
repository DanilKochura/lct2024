import json

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon

from db.DB import DB

db = DB()
print(db.query("INSERT into ships_icemaps"))
exit()


"""

Скрипт для получения ледовой карты в формате GeoJson для фронта

"""




# Шаг дискретизации сетки
step = 10



# Загрузка Excel файла
file_path = 'data/IntegrVelocity.xlsx'
xl = pd.ExcelFile(file_path)

# Чтение координат
lon_df = xl.parse(xl.sheet_names[0])  # Первый лист: долготы
lat_df = xl.parse(xl.sheet_names[1])  # Второй лист: широты

# Считываем данные по ледовой обстановке с остальных листов
data_frames = []
for sheet in xl.sheet_names[2:]:
    df = xl.parse(sheet)
    data_frames.append(df)


# Создание GeoDataFrame
all_polygons = []
all_densities = []

for idx, df in enumerate(data_frames):
    polygons = []
    densities = []

    for i in range(0, len(lon_df) - 1, step):
        for j in range(0, len(lon_df.columns) - 1, step):
            if i + step < len(lon_df) and j + step < len(lon_df.columns):
                # Определяем координаты вершин ячейки
                polygon = Polygon([
                    (lon_df.iloc[i, j], lat_df.iloc[i, j]),
                    (lon_df.iloc[i, j + step], lat_df.iloc[i, j + step]),
                    (lon_df.iloc[i + step, j + step], lat_df.iloc[i + step, j + step]),
                    (lon_df.iloc[i + step, j], lat_df.iloc[i + step, j])
                ], )
                polygons.append(polygon)
                densities.append(df.iloc[i, j])

    all_polygons.append(polygons)
    all_densities.append(densities)

# Создаем GeoDataFrame для каждого временного интервала и сохраняем в GeoJSON
    for idx, (polygons, densities) in enumerate(zip(all_polygons, all_densities)):
        grid_gdf = gpd.GeoDataFrame({'geometry': polygons, 'density': densities}, crs="EPSG:4326")
        grid_gdf.to_file(f'geojson/step_{str(step)}/ice_density_grid_{idx}.geojson', driver='GeoJSON')

    json_file_path = "geojson/step_"+str(step)+"/sheets.json"
    with open(json_file_path, 'w') as json_file:
        json.dump(xl.sheet_names[2:], json_file, indent=4)
