<?php
class Database {
    private $db_file = __DIR__ . '/../data/planify.db';
    private $pdo;
    
    public function __construct() {
        $this->ensureDataDirectory();
        $this->connect();
        $this->createTables();
    }
    
    private function ensureDataDirectory() {
        $dir = dirname($this->db_file);
        if (!file_exists($dir)) {
            mkdir($dir, 0755, true);
        }
    }
    
    private function connect() {
        try {
            $this->pdo = new PDO("sqlite:{$this->db_file}");
            $this->pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $this->pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        } catch (PDOException $e) {
            die(json_encode(['success' => false, 'error' => 'Database connection failed']));
        }
    }
    
    private function createTables() {
        // Users table (coins)
        $this->pdo->exec("
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 15
            )
        ");
        
        // Schedules table
        $this->pdo->exec("
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                notes TEXT,
                color TEXT DEFAULT 'lavender',
                days TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ");
        
        // Tasks table
        $this->pdo->exec("
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT NOT NULL,
                due_time TEXT DEFAULT '23:59',
                category TEXT DEFAULT 'Personal',
                priority TEXT DEFAULT 'low',
                done INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ");
        
        // Ensure default user exists
        $stmt = $this->pdo->query("SELECT COUNT(*) FROM users");
        if ($stmt->fetchColumn() == 0) {
            $this->pdo->exec("INSERT INTO users (coins) VALUES (15)");
        }
    }
    
    public function getConnection() {
        return $this->pdo;
    }
}

$db = new Database();
$pdo = $db->getConnection();
?>