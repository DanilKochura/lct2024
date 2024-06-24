mapboxgl.accessToken = 'pk.eyJ1Ijoia29jaHVyYWRhbmlsIiwiYSI6ImNsd3oxMnhsNDAyb20ybHNmemNpZGVvYzIifQ.QfmPfn0lmXAucuhEG_X4lQ';

let step = 1;
const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/navigation-night-v1',
    center: [105, 70],
    zoom: 3.2
});


function formatDate(date) {
    const optionsDate = {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    };
    const optionsTime = {
        hour: '2-digit',
        minute: '2-digit'
    };

    const formattedDate = date.toLocaleDateString('ru-RU', optionsDate);
    const formattedTime = date.toLocaleTimeString('ru-RU', optionsTime);

    return `${formattedDate} ${formattedTime}`;
}

let shipsData = [];
let points = [];
lines = [];
const dateStrings = [
    "27-Feb-2022",
    "10-Mar-2022",
    "17-Mar-2022",
    "24-Mar-2022",
    "31-Mar-2022",
    "02-Apr-2022",
    "07-Apr-2022",
    "14-Apr-2022",
    "21-Apr-2022",
    "28-Apr-2022",
    "05-May-2022",
    "12-May-2022",
    "19-May-2022",
    "26-May-2022"
];

const dateArray = dateStrings.map(dateString => new Date(dateString));

console.log(dateArray);
let dateindex = 0
var myDate = new Date("2022-02-27T00:00:00Z");
let time = 0;
let globalTime = myDate.getTime();
let speedMultiplier = 1; // Начальная скорость 1x
let fps = 50;

map.on('load', function () {
    const local = 'http://localhost:63342/hackathon';
    fetch(/*local+*/'/api/getGraph')
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
            data: `static/geojson/s${step}/ice_density_grid_${i}.geojson`
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
        $('#timer-date').text(formatDate(myDate));
        // console.log(globalTime, dateArray[dateindex].getTime())
        if (globalTime >= dateArray[dateindex].getTime()) {
            dateindex++
            time = 0;
            const nextIndex = (currentIceDensityIndex + 1) % 10;
            map.setLayoutProperty(`ice-density-layer-${currentIceDensityIndex}`, 'visibility', 'none');
            map.setLayoutProperty(`ice-density-layer-${nextIndex}`, 'visibility', 'visible');
            currentIceDensityIndex = nextIndex;
            $.SOW.core.toast.show('warning', '', `Изменилась ледовая обстановка`, 'top-right', 4000, true);

        } else {
            // console.log('no')
            // console.log(time)
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
    constructor(map, route, name, speed, startTime, type, ice_class) {
        this.ice_class = ice_class
        this.map = map;
        this.route = route.map(point => ({...point, time: new Date(point.date).getTime()}));
        this.name = name;
        this.speed = speed;
        this.startTime = new Date(startTime).getTime();
        this.currentPosition = 0;
        this.segment = -2

        const shipIcon = document.createElement('div');
        shipIcon.className = type === "ice" ? 'icebreaker-icon' : 'ship-icon';

        this.shipFeature = new mapboxgl.Marker(shipIcon)
            .setLngLat(route[0].coords)
            .setPopup(new mapboxgl.Popup().setHTML(`<h3>${name}</h3><p>${this.ice_class}</p>`))
            .addTo(map);

        $.SOW.core.toast.show('success', '', `Корабль ${name} начал плавание`, 'top-right', 4000, true);
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

            if (segmentIndex !== this.segment) {
                if( segmentIndex < this.route.length - 2)
                {
                    let convoy = "<p class='m-0'>...пусто...</p>";
                    if (this.route[segmentIndex+1].convoy) {
                        if (this.route[segmentIndex+1].convoy.length > 0) {
                            convoy = "<ul>"
                            console.log( this.route[segmentIndex+1].convoy)
                            let listItems = this.route[segmentIndex-1].convoy.map(item => `<li>${item}</li>`).join('');
                            for (let index = 0; index < this.route[segmentIndex+1].convoy.length; index++) {
                                convoy += "<li>" + this.route[segmentIndex+1].convoy[index] + "</li>"
                            }
                            console.log(convoy)
                            convoy += listItems+"</ul>"

                        }
                    }
                    let popup = this.shipFeature.getPopup()
                    this.shipFeature.setPopup(popup.setHTML(`<h3>${this.name}</h3><p class="m-0">${this.ice_class}</p><p class="mb-0">Конвой: </p>` + convoy))
                }


                this.segment = segmentIndex
            }

            if (segmentIndex === -1) {
                this.shipFeature.setLngLat(this.route[pathLength - 1].coords);
                this.updateStatus("завершено");
                $.SOW.core.toast.show('primary', '', `Корабль ${this.name} завершил плавание`, 'top-right', 4000, true);
                this.destroy()
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
        // url: '/ships_all.json',
        url: 'static/json/ships_all.json',
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            shipsData = data;
            const shipStatusList = $('#ship-status-list');
            shipsData.forEach(ship => {
                let span = '<span class="badge bg-secondary-soft">ожидает</span>';
                const listItem = $('<div class="d-flex justify-content-between my-2 align-items-center" ></div>');
                listItem.html('<div class="col-7">'+ship.name+'</div>' + '<div class="col-2" id="status-'+ship.id+'">'+span+'</div>'+"<button data-id="+ship.id+" class=\"round-button  btn-modal-open\">\n" +
                    "        <svg xmlns=\"http://www.w3.org/2000/svg\" fill=\"currentColor\" class=\"bi bi-calendar4-range\" viewBox=\"0 0 16 16\">  \n" +
                    "            <path d=\"M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM2 2a1 1 0 0 0-1 1v1h14V3a1 1 0 0 0-1-1H2zm13 3H1v9a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V5z\"></path>  \n" +
                    "            <path d=\"M9 7.5a.5.5 0 0 1 .5-.5H15v2H9.5a.5.5 0 0 1-.5-.5v-1zm-2 3v1a.5.5 0 0 1-.5.5H1v-2h5.5a.5.5 0 0 1 .5.5z\"></path>\n" +
                    "        </svg>\n" +
                    "    </button>");
                shipStatusList.append(listItem);
            });
            console.log(shipsData)
            $('.btn-modal-open').on('click', function () {
                let ship = shipsData.find(item => item['id'] === $(this).data('id'))
                let string = "<li>\n" +
                    "                        <h3 class=\"mb-5\" id=\"ship_map_title\">\n" +
                    "                            Маршрут " + ship.name+
                    "                        </h3>\n" +
                    "                    </li>"
                    for(let i = 0; i < ship.route.length; i++){
                        route = ship.route[i]
                        let added = ""
                        if(i < ship.route.length - 1)
                        {
                            route_next = ship.route[i+1]
                            if(route_next.waiting === true) added+="Ожидаю "+Math.round(route_next.time)+" часов"
                            else if (route_next.provided === true) added+="Под проводкой"
                        } else
                        {
                            added = "Конечная точка"
                        }
                        string+= "<li class=\"pb-5\">\n" +
                            "\n" +
                            "                        <h4 class=\"sow-timeline-title fw-light mb-0 position-relative d-flex align-items-center\">\n" +
                                                        route.port_name+
                            "                        </h4>\n" +
                            "                        <small class=\"text-muted\">"+route.date+"</small>\n" +
                            "\n" +
                            "                        <div class=\"mt-4\">\n" +
                            "                            <p>\n" +
                            added +
                            "                            </p>\n" +
                            "                        </div>\n" +
                            "\n" +
                            "\n" +
                            "                    </li>"
                    }


                $('.sow-timeline').empty().html(string)
                $('#exampleModalSm').modal('show')
            })
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
            const shipInstance = new Ship(map, route, ship.name, ship.speed, ship.date, ship.type, ship.ice_class);
            shipInstance.animate();
        }
    });

    updateShipStatus();
}

function updateShipStatus() {
    shipsData.forEach(ship => {
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
        const listItem = $('#status-'+ship.id);
        listItem.html(span);
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
        $('#timer-date').text(formatDate(myDate));
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
        speedMultiplier = 20
        $('.btn-speed').removeClass('btn-dark')
        $('#speed-10x').addClass('btn-dark')

    });



});
