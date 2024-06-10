<?php
$conn = new mysqli('localhost', 'root', '', 'hackathon');
//$conn = new mysqli('localhost', 'root', 'mJve9nuhEI', 'admin_lct');

$res = $conn->query("SELECT * from graph");
$pts = [];
while ($row = $res->fetch_assoc()) {
    $pts[] = [
        'coords' => [(float)$row['longitude'], (float)$row['latitude']],
        'name' => $row['point_name'],
        'rep_id' => $row['rep_id'],
        'id' => $row['id'],
        ];
}
$res = $conn->query("SELECT * from edges");
$lines = [];
$ids = [];
while ($row = $res->fetch_assoc()) {
    $ids[] = ['points' => [(int)$row['start_point'], (int)$row['end_point']], 'length' => $row['length']];
}
echo json_encode(['points' => $pts, 'edges' => $ids]);
?>