<!DOCTYPE html>
<html>

<head>
    <script>
        window.onload = function() {
            var d = [];
            var dp = [];
            CanvasJS.addColorSet("custom",
                [//colorSet Array

                "#ff57bb",
                "#fdfffc",
                "#2ec4b6",
                "#e71d36",
                "#ff9f1c",
                "#7fff00",
                "#8d99ae",
                "#6f2dbd"
                ]);
            var chart = new CanvasJS.Chart("chartContainer", {
                animationEnabled: true,
                colorSet: "custom",
                theme: "dark2",
                zoomEnabled: true,
                title: {
                    text: "Sensor 1 Ping (Past 24 Hours)"
                },
                axisX: {
                    valueFormatString: "HH:mm"
                },
                axisY: {
                    maximum: 500
                },
                toolTip: {
                    shared: true,
                    content: "{x} - {name}: {y}ms"
                },
                legend: {
                    cursor: "pointer",
                    verticalAlign: "top",
                    horizontalAlign: "center",
                    dockInsidePlotArea: true,
                    itemclick: toogleDataSeries
                },
                data: d
            });

            function addData(data) {
                for (var i = 0; i < data.length; i++) {
                    dp = []
                    for (var ii = 0; ii < (data[i].dps).length; ii++) {
                        dp.push({
                            x: new Date((data[i]).dps[ii].x * 1000),
                            y: (data[i]).dps[ii].y
                        });
                    }
                    d.push({
                        type: "line",
                        name: data[i].name,
                        showInLegend: true,
                        markerSize: 0,
                        xValueFormatString: "DD MMM HH:mm",
                        dataPoints: dp
                    });
                }
                console.log(d)
                chart.render();

            }

            function toogleDataSeries(e) {
                if (typeof(e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
                    e.dataSeries.visible = false;
                } else {
                    e.dataSeries.visible = true;
                }
                chart.render();
            }

            addData(JSON.parse('<?php echo json_encode(json_decode(file_get_contents("http://127.0.0.1:5000/api/v1/daily-ping?sensor=1")))?>'))
            
            var d2 = [];
            var dp2 = [];
            var chart2 = new CanvasJS.Chart("chartContainer2", {
                animationEnabled: true,
                colorSet: "custom",
                theme: "dark2",
                zoomEnabled: true,
                title: {
                    text: "Overal DNS Outage (Past 24 Hours)"
                },
                axisX: {
                    valueFormatString: "HH:mm"
                },
                axisY: {
                    includeZero: true,
                },
                toolTip: {
                    shared: true,
                    content: "{x} - {name}: {y}"
                },
                legend: {
                    cursor: "pointer",
                    verticalAlign: "top",
                    horizontalAlign: "center",
                    dockInsidePlotArea: true,
                    itemclick: toogleDataSeries2
                },
                data: d2
            });
        
            function addData2(data) {
                for (var i = 0; i < data.length; i++) {
                    dp2 = []
                    for (var ii = 0; ii < (data[i].dps).length; ii++) {
                        dp2.push({
                            x: new Date((data[i]).dps[ii].x * 1000),
                            y: (data[i]).dps[ii].y
                        });
                    }
                    d2.push({
                        type: "column",
                        name: data[i].name,
                        showInLegend: true,
                        markerSize: 0,
                        xValueFormatString: "DD MMM HH:mm",
                        dataPoints: dp2
                    });
                }
                console.log(d2)
                chart2.render();

            }

            function toogleDataSeries2(e) {
                if (typeof(e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
                    e.dataSeries.visible = false;
                } else {
                    e.dataSeries.visible = true;
                }
                chart2.render();
            }

            addData2(JSON.parse('<?php echo json_encode(json_decode(file_get_contents("http://127.0.0.1:5000/api/v1/dns-outage")))?>'))

        }
    </script>
</head>

<body style="background-color: #1a1a1a;">
    <div id="chartContainer" style="width: 100%; height: 300px;display: inline-block;"></div>
    <div id="chartContainer2" style="width: 100%; height: 300px;display: inline-block;"></div>
    <script src="https://canvasjs.com/assets/script/canvasjs.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
</body>

</html>