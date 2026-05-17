<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once 'db.php';

$action = $_GET['action'] ?? '';

try {
    switch ($action) {
        case 'getUserData':
            getUserData($pdo);
            break;
        case 'getDashboard':
            getDashboard($pdo);
            break;
        case 'getSchedules':
            getSchedules($pdo);
            break;
        case 'getTasks':
            getTasks($pdo);
            break;
        case 'addSchedule':
            addSchedule($pdo);
            break;
        case 'addTask':
            addTask($pdo);
            break;
        case 'toggleTask':
            toggleTask($pdo);
            break;
        case 'deleteTask':
            deleteTask($pdo);
            break;
        case 'deleteSchedule':
            deleteSchedule($pdo);
            break;
        case 'updateCoins':
            updateCoins($pdo);
            break;
        case 'spendCoins':
            spendCoins($pdo);
            break;
        default:
            echo json_encode(['success' => false, 'error' => 'Invalid action']);
    }
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}

function getUserData($pdo) {
    $stmt = $pdo->query("SELECT coins FROM users WHERE id = 1");
    $user = $stmt->fetch();
    echo json_encode(['success' => true, 'data' => ['coins' => $user['coins']]]);
}

function getDashboard($pdo) {
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM tasks WHERE done = 0");
    $pending = $stmt->fetch()['count'];
    
    $stmt = $pdo->query("SELECT COUNT(*) as count FROM schedules");
    $scheduleCount = $stmt->fetch()['count'];
    
    $stmt = $pdo->query("
        SELECT COUNT(*) as count FROM tasks 
        WHERE done = 0 
        AND datetime(due_date || ' ' || due_time) > datetime('now')
        AND datetime(due_date || ' ' || due_time) < datetime('now', '+1 day')
    ");
    $urgent = $stmt->fetch()['count'];
    
    $stmt = $pdo->query("
        SELECT id, title, priority, due_date, due_time FROM tasks 
        WHERE done = 0 
        ORDER BY datetime(due_date || ' ' || due_time) ASC 
        LIMIT 5
    ");
    $upcoming = [];
    while ($row = $stmt->fetch()) {
        $upcoming[] = [
            'id' => $row['id'],
            'title' => $row['title'],
            'priority' => $row['priority'],
            'countdownClass' => getCountdownClass($row['due_date'], $row['due_time']),
            'countdownText' => getCountdownText($row['due_date'], $row['due_time'])
        ];
    }
    
    $todayName = date('D');
    $todayMap = ['Mon' => 'Mon', 'Tue' => 'Tue', 'Wed' => 'Wed', 'Thu' => 'Thu', 'Fri' => 'Fri', 'Sat' => 'Sat', 'Sun' => 'Sun'];
    $today = $todayMap[$todayName] ?? 'Mon';
    $stmt = $pdo->prepare("
        SELECT title, start_time, end_time FROM schedules 
        WHERE days LIKE ?
        ORDER BY start_time ASC
    ");
    $stmt->execute(["%$today%"]);
    $todaySchedules = $stmt->fetchAll();
    
    echo json_encode([
        'success' => true,
        'data' => [
            'pendingTasks' => $pending,
            'scheduleCount' => $scheduleCount,
            'urgentCount' => $urgent,
            'upcomingTasks' => $upcoming,
            'todaySchedules' => $todaySchedules
        ]
    ]);
}

function getSchedules($pdo) {
    $stmt = $pdo->query("SELECT id, title, start_time as start, end_time as end, notes, color, days FROM schedules ORDER BY start_time");
    echo json_encode(['success' => true, 'data' => $stmt->fetchAll()]);
}

function getTasks($pdo) {
    $stmt = $pdo->query("SELECT id, title, description as desc, due_date as date, due_time as time, category, priority, done FROM tasks ORDER BY done ASC, datetime(due_date || ' ' || due_time) ASC");
    $tasks = $stmt->fetchAll();
    foreach ($tasks as &$task) {
        $task['countdownClass'] = getCountdownClass($task['date'], $task['time']);
        $task['countdownText'] = getCountdownText($task['date'], $task['time']);
    }
    echo json_encode(['success' => true, 'data' => $tasks]);
}

function addSchedule($pdo) {
    $input = json_decode(file_get_contents('php://input'), true);
    $stmt = $pdo->prepare("
        INSERT INTO schedules (title, start_time, end_time, notes, color, days) 
        VALUES (?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([
        $input['title'],
        $input['start'],
        $input['end'] ?? null,
        $input['notes'] ?? null,
        $input['color'] ?? 'lavender',
        $input['days']
    ]);
    echo json_encode(['success' => true, 'data' => ['id' => $pdo->lastInsertId()]]);
}

function addTask($pdo) {
    $input = json_decode(file_get_contents('php://input'), true);
    $stmt = $pdo->prepare("
        INSERT INTO tasks (title, description, due_date, due_time, category, priority) 
        VALUES (?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([
        $input['title'],
        $input['desc'] ?? null,
        $input['date'],
        $input['time'] ?? '23:59',
        $input['category'] ?? 'Personal',
        $input['priority'] ?? 'low'
    ]);
    echo json_encode(['success' => true, 'data' => ['id' => $pdo->lastInsertId()]]);
}

function toggleTask($pdo) {
    $input = json_decode(file_get_contents('php://input'), true);
    $stmt = $pdo->prepare("UPDATE tasks SET done = ? WHERE id = ?");
    $stmt->execute([$input['done'] ? 1 : 0, $input['id']]);
    
    $reward = 0;
    if ($input['done']) {
        $stmt2 = $pdo->prepare("SELECT priority FROM tasks WHERE id = ?");
        $stmt2->execute([$input['id']]);
        $task = $stmt2->fetch();
        $reward = $task['priority'] == 'high' ? 10 : ($task['priority'] == 'med' ? 7 : 5);
        $stmt3 = $pdo->prepare("UPDATE users SET coins = coins + ? WHERE id = 1");
        $stmt3->execute([$reward]);
    }
    
    echo json_encode(['success' => true, 'data' => ['reward' => $reward]]);
}

function deleteTask($pdo) {
    $input = json_decode(file_get_contents('php://input'), true);
    $stmt = $pdo->prepare("DELETE FROM tasks WHERE id = ?");
    $stmt->execute([$input['id']]);
    echo json_encode(['success' => true]);
}

function deleteSchedule($pdo) {
    $input = json_decode(file_get_contents('php://input'), true);
    $stmt = $pdo->prepare("DELETE FROM schedules WHERE id = ?");
    $stmt->execute([$input['id']]);
    echo json_encode(['success' => true]);
}

function updateCoins($pdo) {
    $input = json_decode(file_get_contents('php://input'), true);
    $stmt = $pdo->prepare("UPDATE users SET coins = coins + ? WHERE id = 1");
    $stmt->execute([$input['amount']]);
    $stmt2 = $pdo->query("SELECT coins FROM users WHERE id = 1");
    $coins = $stmt2->fetch()['coins'];
    echo json_encode(['success' => true, 'data' => ['coins' => $coins]]);
}

function spendCoins($pdo) {
    $input = json_decode(file_get_contents('php://input'), true);
    $amount = $input['amount'];
    $stmt = $pdo->query("SELECT coins FROM users WHERE id = 1");
    $coins = $stmt->fetch()['coins'];
    if ($coins >= $amount) {
        $stmt2 = $pdo->prepare("UPDATE users SET coins = coins - ? WHERE id = 1");
        $stmt2->execute([$amount]);
        $stmt3 = $pdo->query("SELECT coins FROM users WHERE id = 1");
        $newCoins = $stmt3->fetch()['coins'];
        echo json_encode(['success' => true, 'data' => ['coins' => $newCoins]]);
    } else {
        echo json_encode(['success' => false, 'error' => 'Insufficient coins']);
    }
}

function getCountdownClass($date, $time) {
    $diff = (new DateTime($date . ' ' . $time))->getTimestamp() - time();
    if ($diff < 0) return 'past';
    if ($diff < 21600) return 'urgent';
    if ($diff < 86400) return 'warning';
    return 'safe';
}

function getCountdownText($date, $time) {
    $diff = (new DateTime($date . ' ' . $time))->getTimestamp() - time();
    if ($diff < 0) return 'Overdue';
    $hours = floor($diff / 3600);
    if ($hours < 6) return $hours . 'h left';
    if ($hours < 24) return $hours . 'h';
    return floor($hours / 24) . 'd left';
}
?>