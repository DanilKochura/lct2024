    mapboxgl.accessToken = 'pk.eyJ1Ijoia29jaHVyYWRhbmlsIiwiYSI6ImNsd3oxMnhsNDAyb20ybHNmemNpZGVvYzIifQ.QfmPfn0lmXAucuhEG_X4lQ';

    let step = 1;
    const map = new mapboxgl.Map({
        container: 'map',
        // style: 'mapbox://styles/mapbox/standard',
        style: 'mapbox://styles/mapbox/navigation-night-v1',
        center: [105, 70],
        zoom: 3
    });

    let shipsData = [];
    let points = [];
    lines = [];
    let sheets = [
        "03-Mar-2020",
        "10-Mar-2020",
        "17-Mar-2020",
        "24-Mar-2020",
        "31-Mar-2020",
        "02-Apr-2020",
        "07-Apr-2020",
        "14-Apr-2020",
        "21-Apr-2020",
        "28-Apr-2020",
        "05-May-2020",
        "12-May-2020",
        "19-May-2020",
        "26-May-2020"
    ];

    var myDate = new Date("2022-03-01T00:00:00Z");
    let time = 0;
    let globalTime = myDate.getTime();

    map.on('load', function () {
        const local = 'http://localhost:63342/hackathon';
        fetch(/*local+*/'/api/getGraph.php')
            .then(response => response.json())
            .then(graphData => {
                graphData.points.forEach(point => {
                    new mapboxgl.Marker()
                        .setLngLat(point.coords)
                        .setPopup(new mapboxgl.Popup().setHTML(`<h3>${point.name}</h3>${point.coords[1]},${point.coords[0]}</p>`))
                        .addTo(map);
                });

                graphData.edges.forEach(edge => {
                    const startPoint = graphData.points[edge.points[0]].coords;
                    const endPoint = graphData.points[edge.points[1]].coords;
                    const coordinates = [startPoint, endPoint];

                    map.addSource(`line-${edge.points[0]}-${edge.points[1]}`, {
                        'type': 'geojson',
                        'data': {
                            'type': 'Feature',
                            'properties': {},
                            'geometry': {
                                'type': 'LineString',
                                'coordinates': coordinates
                            }
                        }
                    });

                    map.addLayer({
                        'id': `line-${edge.points[0]}-${edge.points[1]}`,
                        'type': 'line',
                        'source': `line-${edge.points[0]}-${edge.points[1]}`,
                        'layout': {
                            'line-join': 'round',
                            'line-cap': 'round'
                        },
                        'paint': {
                            'line-color': '#888',
                            'line-opacity': 0.3,
                            'line-width': 5
                        }
                    });

                    map.on('click', `line-${edge.points[0]}-${edge.points[1]}`, function (e) {

                        const coordinates = e.lngLat;
                        new mapboxgl.Popup()
                            .setLngLat(coordinates)
                            .setHTML(`<p><b>${edge.length}</b> мили</p>`)
                            .addTo(map);
                        if (lines[`line-${edge.points[0]}-${edge.points[1]}`] === 1)
                        {
                            lines[`line-${edge.points[0]}-${edge.points[1]}`] = 0
                            map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-color', '#ff0000');
                            map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-opacity', 1);
                            map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-width', 10);
                        } else
                        {
                            lines[`line-${edge.points[0]}-${edge.points[1]}`] = 1
                            map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-color', '#888');
                            map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-opacity', 0.5);
                            map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-width', 5);
                        }
                        });

                    map.on('mouseenter', `line-${edge.points[0]}-${edge.points[1]}`, function () {
                        map.getCanvas().style.cursor = 'pointer';
                    });

                    map.on('mouseleave', `line-${edge.points[0]}-${edge.points[1]}`, function () {
                        map.getCanvas().style.cursor = '';
                    });
                });

                points = graphData.points;
            })
            .catch(error => console.error('Ошибка загрузки данных о графе:', error));

        const co = 14;
        for (let i = 0; i < co; i++) {
            map.addSource(`ice-density-${i}`, {
                type: 'geojson',
                data: `/geojson/s${step}/ice_density_grid_${i}.geojson`
            });

            map.addLayer({
                id: `ice-density-layer-${i}`,
                type: 'fill',
                source: `ice-density-${i}`,
                paint: {
                    'fill-color': [
                        'interpolate',
                        ['linear'],
                        ['get', 'density'],
                        // 0, 'rgba(1,16,14,0.1)',
                        // 7, '#8f1b44',
                        // 12, '#AA5E79',
                        // 15, '#A2719B',
                        // 17, '#8B88B6',
                        // 19, '#669EC4',
                        // 20, '#3BB3C3',
                        // 24, '#55c0ce',
                        0, 'rgba(1,16,14,0.1)',
                        10, '#5d0a25',
                        15, 'rgb(246,192,192)',
                        20, '#3BB3C3',
                    ],
                    'fill-opacity': 0.5
                },
                layout: {
                    'visibility': i === 0 ? 'visible' : 'none'
                }
            });
        }

        let currentIceDensityIndex = 0;
        time = 0;

        function toggleIceDensity() {
            myDate = new Date(myDate.getTime() + 60 * 60 * 1000);
            globalTime += 60 * 60 * 1000;
            let date = myDate.toISOString().split('T');
            $('#timer-date').text(date[0] + ' ' + myDate.getHours() + ':' + myDate.getMinutes());

            if (time + 60 * 60 * 1000 === 7 * 24 * 60 * 60 * 1000) {
                time = 0;
                const nextIndex = (currentIceDensityIndex + 1) % 10;
                map.setLayoutProperty(`ice-density-layer-${currentIceDensityIndex}`, 'visibility', 'none');
                map.setLayoutProperty(`ice-density-layer-${nextIndex}`, 'visibility', 'visible');
                currentIceDensityIndex = nextIndex;
            } else {
                time += 60 * 60 * 1000;
            }
        }

        setInterval(toggleIceDensity, 1000);

        var markers = [
            { coordinates: [69.9, 179], color: 'red' },
            { coordinates: [69.5, 33.75], color: 'red' },
            { coordinates: [77.3, 67.7], color: 'red' },
            { coordinates: [74.6, 63.9], color: 'red' }
        ];

        markers.forEach(function (marker) {
            var markerElement = document.createElement('div');
            markerElement.style.width = '20px';
            markerElement.style.height = '20px';
            markerElement.style.background = marker.color;
            markerElement.style.borderRadius = '50%';
            markerElement.style.zIndex = 10;

            new mapboxgl.Marker(markerElement)
                .setLngLat(marker.coordinates.reverse())
                .addTo(map);
        });
    });

    class Ship {
        constructor(map, coordinates, name, speed, startTime) {
            this.map = map;
            this.coordinates = coordinates;
            this.name = name;
            this.speed = speed; // узлы
            this.startTime = new Date(startTime).getTime();
            this.currentPosition = 0;

            const shipIcon = document.createElement('div');
            shipIcon.className = 'ship-icon';

            this.shipFeature = new mapboxgl.Marker(shipIcon)
                .setLngLat(coordinates[0])
                .setPopup(new mapboxgl.Popup().setHTML(`<h3>${name}</h3><p>Скорость ${speed} узлов</p>`))
                .addTo(map);
        }

        animate() {
            const animateStep = () => {
                const elapsedTime = (globalTime - this.startTime) / 1000 / 3600; // Пройденное время в часах
                const distanceCovered = elapsedTime * this.speed; // Пройденное расстояние в морских милях
                const totalDistance = this.calculateTotalDistance();

                if (distanceCovered >= totalDistance) {
                    this.shipFeature.setLngLat(this.coordinates[this.coordinates.length - 1]);
                    return;
                }

                let segmentDistanceCovered = 0;
                let segmentStart = this.coordinates[0];
                let segmentEnd = this.coordinates[1];

                for (let i = 1; i < this.coordinates.length; i++) {
                    const segmentDistance = this.getDistance(this.coordinates[i - 1], this.coordinates[i]);
                    if (segmentDistanceCovered + segmentDistance >= distanceCovered) {
                        segmentStart = this.coordinates[i - 1];
                        segmentEnd = this.coordinates[i];
                        break;
                    }
                    segmentDistanceCovered += segmentDistance;
                }

                const segmentProgress = (distanceCovered - segmentDistanceCovered) / this.getDistance(segmentStart, segmentEnd);
                const currentCoords = this.interpolateCoords(segmentStart, segmentEnd, segmentProgress);

                this.shipFeature.setLngLat(currentCoords);

                requestAnimationFrame(animateStep);
            };

            requestAnimationFrame(animateStep);
        }

        calculateTotalDistance() {
            let totalDistance = 0;
            for (let i = 0; i < this.coordinates.length - 1; i++) {
                totalDistance += this.getDistance(this.coordinates[i], this.coordinates[i + 1]);
            }
            return totalDistance;
        }

        getDistance(coord1, coord2) {
            const [lon1, lat1] = coord1;
            const [lon2, lat2] = coord2;
            const R = 6371e3; // Радиус Земли в метрах
            const φ1 = lat1 * Math.PI / 180;
            const φ2 = lat2 * Math.PI / 180;
            const Δφ = (lat2 - lat1) * Math.PI / 180;
            const Δλ = (lon2 - lon1) * Math.PI / 180;

            const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
                Math.cos(φ1) * Math.cos(φ2) *
                Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

            const d = R * c;
            return d / 1852; // Переводим метры в морские мили
        }

        interpolateCoords(startCoords, endCoords, ratio) {
            const lat = startCoords[1] + (endCoords[1] - startCoords[1]) * ratio;
            const lon = startCoords[0] + (endCoords[0] - startCoords[0]) * ratio;
            return [lon, lat];
        }
    }

    function loadShips() {
        $.ajax({
            url: '/test_unescaped.json',
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                shipsData = data;
            },
            error: function (xhr, status, error) {
                console.error('Ошибка при загрузке данных о кораблях:', error);
            }
        });
    }

    function checkAndStartShips() {
        // Перебираем все корабли
        shipsData.forEach(ship => {
            // Проверяем, если корабль еще не был запущен и текущее время больше или равно времени отправления корабля
            if (!ship.started && new Date(ship.date) <= new Date(globalTime)) {
                ship.started = true; // Помечаем корабль как запущенный
                const coordinates = ship.route[0]; // Получаем начальные координаты корабля
                const shipInstance = new Ship(map, coordinates, ship.name, ship.speed, ship.date); // Создаем экземпляр корабля
                shipInstance.start(); // Запускаем корабль
            }
        });
    }

    setInterval(checkAndStartShips, 1000 * 12);

    $(document).ready(function () {
        loadShips();

        $('#menu-toggle').click(function () {
            $('#floating-menu').toggleClass('collapsed');
            $(this).toggleClass('collapsed');
        });
    });
