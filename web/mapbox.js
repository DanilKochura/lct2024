mapboxgl.accessToken = 'pk.eyJ1Ijoia29jaHVyYWRhbmlsIiwiYSI6ImNsd3oxMnhsNDAyb20ybHNmemNpZGVvYzIifQ.QfmPfn0lmXAucuhEG_X4lQ';

let step = 1;
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/navigation-night-v1',
    center: [105, 70],
    zoom: 3
});

let shipsData = [];
let points = [];
lines = [];

var myDate = new Date("2022-02-27T00:00:00Z");
let time = 0;
let globalTime = myDate.getTime();
let speedMultiplier = 1; // Начальная скорость 1x
let fps = 50;

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
                        .setHTML(`<p><b>${edge.length}</b> мили</p>  (#${edge.id})`)
                        .addTo(map);
                    if (lines[`line-${edge.points[0]}-${edge.points[1]}`] === 1) {
                        lines[`line-${edge.points[0]}-${edge.points[1]}`] = 0
                        map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-color', '#ff0000');
                        map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-opacity', 1);
                        map.setPaintProperty(`line-${edge.points[0]}-${edge.points[1]}`, 'line-width', 10);
                    } else {
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
                    0, 'rgba(1,16,14,0.1)',
                    7, '#8f1b44',
                    12, '#AA5E79',
                    15, '#A2719B',
                    17, '#8B88B6',
                    19, '#669EC4',
                    20, '#3BB3C3',
                    24, '#55c0ce',
                ],
                'fill-opacity': 0.1
            },
            layout: {
                'visibility': i === 0 ? 'visible' : 'none'
            }
        });
    }

    let currentIceDensityIndex = 0;
    time = 0;

    function toggleIceDensity() {
        myDate = new Date(myDate.getTime() + 60 * 1000 * speedMultiplier);
        globalTime += 60 * 1000 * speedMultiplier;
        let date = myDate.toISOString().split('T');
        $('#timer-date').text(date[0] + ' ' + myDate.getHours() + ':' + myDate.getMinutes());

        if (time + 60 * 1000 * speedMultiplier === 7 * 24 * 60 * 60 * 1000) {
            time = 0;
            const nextIndex = (currentIceDensityIndex + 1) % 10;
            map.setLayoutProperty(`ice-density-layer-${currentIceDensityIndex}`, 'visibility', 'none');
            map.setLayoutProperty(`ice-density-layer-${nextIndex}`, 'visibility', 'visible');
            currentIceDensityIndex = nextIndex;
        } else {
            time += 60 * 1000 * speedMultiplier;
        }
    }

    setInterval(toggleIceDensity, fps);

    // var markers = [
    //     {coordinates: [69.9, 179], color: 'red'},
    //     {coordinates: [69.5, 33.75], color: 'red'},
    //     {coordinates: [77.3, 67.7], color: 'red'},
    //     {coordinates: [74.6, 63.9], color: 'red'}
    // ];
    //
    // markers.forEach(function (marker) {
    //     const shipIcon = document.createElement('div');
    //     shipIcon.className = 'icebreaker-icon';
    //     new mapboxgl.Marker(shipIcon)
    //         .setLngLat(marker.coordinates.reverse())
    //         .addTo(map);
    // });
});

class Ship {
    constructor(map, route, name, speed, startTime, type) {
        this.map = map;
        this.route = route.map(point => ({ ...point, time: new Date(point.date).getTime() }));
        this.name = name;
        this.speed = speed;
        this.startTime = new Date(startTime).getTime();
        this.currentPosition = 0;

        const shipIcon = document.createElement('div');
        shipIcon.className = type === "ice" ? 'icebreaker-icon' : 'ship-icon';

        this.shipFeature = new mapboxgl.Marker(shipIcon)
            .setLngLat(route[0].coords)
            .setPopup(new mapboxgl.Popup().setHTML(`<h3>${name}</h3><p>Скорость ${speed} узлов</p>`))
            .addTo(map);

        $.SOW.core.toast.show('success', '',`Корабль ${name} начал плавание`, 'top-right', 4000, true);
        this.animate();
    }

    animate() {
        const pathLength = this.route.length;

        const interpolateCoords = (startCoords, endCoords, ratio) => {
            const lat = startCoords[1] + (endCoords[1] - startCoords[1]) * ratio;
            const lng = startCoords[0] + (endCoords[0] - startCoords[0]) * ratio;
            return [lng, lat];
        };

        const animateStep = () => {
            const currentTime = globalTime;
            let segmentIndex = -1;

            for (let i = 0; i < pathLength - 1; i++) {
                if (currentTime >= this.route[i].time && currentTime < this.route[i + 1].time) {
                    segmentIndex = i;
                    break;
                }
            }

            if (segmentIndex === -1) {
                this.shipFeature.setLngLat(this.route[pathLength - 1].coords);
                this.updateStatus("завершено");
                return;
            }

            const segmentStart = this.route[segmentIndex];
            const segmentEnd = this.route[segmentIndex + 1];
            const segmentElapsed = currentTime - segmentStart.time;
            const segmentTotal = segmentEnd.time - segmentStart.time;
            const segmentRatio = segmentElapsed / segmentTotal;

            const currentCoords = interpolateCoords(segmentStart.coords, segmentEnd.coords, segmentRatio);
            this.shipFeature.setLngLat(currentCoords);

            this.animationFrameId = requestAnimationFrame(animateStep);
        };

        this.animationFrameId = requestAnimationFrame(animateStep);
    }

    updateStatus(newStatus) {
        this.status = newStatus;
        updateShipStatus();
    }

    destroy() {
        cancelAnimationFrame(this.animationFrameId);
        this.shipFeature.remove();
    }
}

function loadShips() {
    $.ajax({
        url: '/ships_all.json',
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            shipsData = data;
            checkAndStartShips();
        },
        error: function (xhr, status, error) {
            console.error('Ошибка при загрузке данных о кораблях:', error);
        }
    });
}

function checkAndStartShips() {
    shipsData.forEach(ship => {
        let date = ship.date;
        ship.date = new Date(date).getTime();
        if (!ship.started && new Date(ship.date) <= new Date(globalTime)) {
            ship.started = true;
            const route = ship.route;
            if (!ship.type) ship.type = "no";
            const shipInstance = new Ship(map, route, ship.name, ship.speed, ship.date, ship.type);
            shipInstance.animate();
        }
    });
    updateShipStatus();
}

function updateShipStatus() {
    const shipStatusList = $('#ship-status-list');
    shipStatusList.empty();

    shipsData.forEach(ship => {
        let status = 'ожидает отплытия';
        let span = '<span class="ml-2 badge bg-secondary-soft">ожидает</span>';
        if (ship.started) {
            const lastPoint = ship.route[ship.route.length - 1];
            if (globalTime >= new Date(lastPoint.date).getTime()) {
                status = 'завершено';
                span = '<span class="ml-2 badge bg-danger-soft">завершено</span>';
            } else {
                status = 'в пути';
                span = '<span class="ml-2 badge bg-success-soft">в пути</span>';
            }
        }
        const listItem = $('<li></li>');
        listItem.text(ship.name + ' ');
        listItem.append(span);
        shipStatusList.append(listItem);
    });
}

$(document).ready(function () {
    loadShips();
    setInterval(checkAndStartShips, 1000);

    $('#menu-toggle').click(function () {
        $('#floating-menu').toggleClass('collapsed');
        $(this).toggleClass('collapsed');
    });

    // Изменение глобального таймера с учетом множителя скорости
    setInterval(() => {
        myDate = new Date(myDate.getTime() + 60 * 1000 * speedMultiplier);
        globalTime += 60 * 1000 * speedMultiplier;
        let date = myDate.toISOString().split('T');
        $('#timer-date').text(date[0] + ' ' + myDate.getHours() + ':' + myDate.getMinutes());
    }, fps);

    // Обработчики для кнопок изменения скорости
    $('#speed-1x').click(() => {
        speedMultiplier = 1
        $('.btn-speed').removeClass('btn-dark')
        $('#speed-1x').addClass('btn-dark')
    });
    $('#speed-2x').click(() => {
        speedMultiplier = 2
        $('.btn-speed').removeClass('btn-dark')
        $('#speed-2x').addClass('btn-dark')
    });
    $('#speed-5x').click(() => {
        speedMultiplier = 5
        $('.btn-speed').removeClass('btn-dark')
        $('#speed-5x').addClass('btn-dark')
    });
    $('#speed-10x').click(() => {
        speedMultiplier = 10
        $('.btn-speed').removeClass('btn-dark')
        $('#speed-10x').addClass('btn-dark')

    });
});
