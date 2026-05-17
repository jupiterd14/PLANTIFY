// ========== PLANIFY FRONTEND ==========
let socket = null;
let currentPriority = 'low';

// Game variables
let gameActive = false;
let gameScore = 0, gameLives = 3, gameLevel = 1;
let bubbles = [], animFrame, lastSpawn = 0, spawnDelay = 1500, speed = 0.7;
let canvas, ctx;
let earnedThisGame = 0;

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
    initSocket();
    initCanvas();
    buildDaysSelector();
    setHeaderDate();
    loadDashboard();
    loadSchedules();
    loadTasks();
    loadUserInfo();
    
    // Set default date for task form
    const today = new Date().toISOString().split('T')[0];
    if (document.getElementById('taskDueDate')) {
        document.getElementById('taskDueDate').value = today;
    }
});

// ========== WEBSOCKET ==========
function initSocket() {
    socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to server');
        showToast('Connected to Planify!');
    });
    
    socket.on('task_completed', (data) => {
        console.log('Task completed:', data);
        if (data.leveled_up) {
            showToast(`Level up! You're now level ${data.new_level}! 🎉`);
        }
        loadUserInfo();
        loadDashboard();
    });
    
    socket.on('task_deleted', () => {
        loadTasks();
        loadDashboard();
    });
}

// ========== API CALLS ==========
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);
    
    try {
        const response = await fetch(endpoint, options);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'API error');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message);
        return null;
    }
}

// ========== USER ==========
async function loadUserInfo() {
    const user = await apiCall('/api/user/');
    if (user) {
        document.getElementById('headerCoins').innerText = user.coins;
        document.getElementById('gameCoinDisplay').innerText = user.coins;
    }
}

// ========== DASHBOARD ==========
async function loadDashboard() {
    const data = await apiCall('/api/user/dashboard');
    if (!data) return;
    
    document.getElementById('dashPending').innerText = data.pending_tasks;
    document.getElementById('dashSchedules').innerText = data.schedule_count;
    document.getElementById('dashUrgent').innerText = data.urgent_count;
    
    // Today's schedules
    const todayDiv = document.getElementById('todayScheduleList');
    if (data.today_schedules && data.today_schedules.length) {
        todayDiv.innerHTML = data.today_schedules.map(s => `
            <div class="item-card schedule">
                <div class="item-details">
                    <div class="item-title">${escapeHtml(s.title)}</div>
                    <div class="item-meta">
                        <span class="badge time">${s.start_time}${s.end_time ? ' - ' + s.end_time : ''}</span>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        todayDiv.innerHTML = '<div class="empty-state">Nothing scheduled today</div>';
    }
}

// ========== TASKS ==========
async function loadTasks() {
    const tasks = await apiCall('/api/tasks/');
    const container = document.getElementById('tasksListContainer');
    
    if (!tasks || !tasks.length) {
        container.innerHTML = '<div class="empty-state">No tasks yet</div>';
        return;
    }
    
    // Update upcoming tasks in dashboard
    const upcoming = tasks.filter(t => !t.done).slice(0, 5);
    const upcomingDiv = document.getElementById('upcomingTasksList');
    if (upcoming.length) {
        upcomingDiv.innerHTML = upcoming.map(t => `
            <div class="item-card ${t.priority}">
                <div class="item-details">
                    <div class="item-title">${escapeHtml(t.title)}</div>
                    <div class="item-meta">
                        <span class="badge ${t.priority}">${t.priority}</span>
                        <span class="badge">${t.due_date}</span>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        upcomingDiv.innerHTML = '<div class="empty-state">No pending tasks</div>';
    }
    
    // Full task list
    const sorted = [...tasks].sort((a, b) => (a.done === b.done ? 0 : a.done ? 1 : -1));
    container.innerHTML = sorted.map(t => `
        <div class="item-card ${t.priority} ${t.done ? 'done' : ''}">
            <div class="item-check">
                <input type="checkbox" ${t.done ? 'checked' : ''} onchange="toggleTask(${t.id}, this.checked)">
            </div>
            <div class="item-details">
                <div class="item-title">${escapeHtml(t.title)}</div>
                <div class="item-meta">
                    <span class="badge ${t.priority}">${t.priority}</span>
                    <span class="badge">${t.due_date} ${t.due_time}</span>
                    ${t.description ? `<div style="font-size:0.75rem;margin-top:5px;">${escapeHtml(t.description)}</div>` : ''}
                </div>
            </div>
            <div class="item-actions">
                <button class="icon-btn" onclick="deleteTask(${t.id})">🗑</button>
            </div>
        </div>
    `).join('');
}

async function addTask() {
    const title = document.getElementById('taskTitle').value.trim();
    if (!title) {
        showToast('Task title required');
        return;
    }
    
    const task = {
        title: title,
        description: document.getElementById('taskDesc').value,
        due_date: document.getElementById('taskDueDate').value || new Date().toISOString().split('T')[0],
        due_time: document.getElementById('taskDueTime').value || '23:59',
        category: document.getElementById('taskCategory').value,
        priority: currentPriority
    };
    
    const result = await apiCall('/api/tasks/', 'POST', task);
    if (result && result.success) {
        showToast('Task added!');
        document.getElementById('taskTitle').value = '';
        document.getElementById('taskDesc').value = '';
        loadTasks();
        loadDashboard();
        switchView('tasks');
    }
}

async function toggleTask(taskId, completed) {
    const result = await apiCall(`/api/tasks/${taskId}`, 'PUT', { done: completed });
    if (result && result.success) {
        if (completed) {
            showCelebration('Task completed! +coins earned');
            playSound(660, 0.2);
            vibrate([50, 100, 50]);
        }
        loadTasks();
        loadDashboard();
        loadUserInfo();
    }
}

async function deleteTask(taskId) {
    const result = await apiCall(`/api/tasks/${taskId}`, 'DELETE');
    if (result && result.success) {
        showToast('Task deleted');
        loadTasks();
        loadDashboard();
    }
}

// ========== SCHEDULES ==========
async function loadSchedules() {
    const schedules = await apiCall('/api/schedules/');
    const container = document.getElementById('scheduleListContainer');
    
    if (!schedules || !schedules.length) {
        container.innerHTML = '<div class="empty-state">No recurring schedules</div>';
        return;
    }
    
    container.innerHTML = schedules.map(s => `
        <div class="item-card schedule">
            <div class="item-details">
                <div class="item-title">${escapeHtml(s.title)}</div>
                <div class="item-meta">
                    <span class="badge time">${s.start_time}${s.end_time ? ' - ' + s.end_time : ''}</span>
                    <span class="badge">${s.days.join(', ')}</span>
                    ${s.notes ? `<span class="badge">${escapeHtml(s.notes)}</span>` : ''}
                </div>
            </div>
            <div class="item-actions">
                <button class="icon-btn" onclick="deleteSchedule(${s.id})">🗑</button>
            </div>
        </div>
    `).join('');
}

async function addSchedule() {
    const title = document.getElementById('schedTitle').value.trim();
    const startTime = document.getElementById('schedStart').value;
    
    if (!title || !startTime) {
        showToast('Title and start time required');
        return;
    }
    
    const days = Array.from(document.querySelectorAll('#daysContainer .day-chip.selected')).map(d => d.innerText);
    const schedule = {
        title: title,
        start_time: startTime,
        end_time: document.getElementById('schedEnd').value,
        notes: document.getElementById('schedNotes').value,
        color: 'lavender',
        days: days.length ? days : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    };
    
    const result = await apiCall('/api/schedules/', 'POST', schedule);
    if (result && result.success) {
        showToast('Schedule saved!');
        document.getElementById('schedTitle').value = '';
        document.getElementById('schedStart').value = '';
        document.getElementById('schedEnd').value = '';
        document.getElementById('schedNotes').value = '';
        loadSchedules();
        loadDashboard();
        switchView('schedule');
    }
}

async function deleteSchedule(scheduleId) {
    const result = await apiCall(`/api/schedules/${scheduleId}`, 'DELETE');
    if (result && result.success) {
        showToast('Schedule deleted');
        loadSchedules();
        loadDashboard();
    }
}

// ========== GAME ==========
function initCanvas() {
    canvas = document.getElementById('bubbleCanvas');
    if (!canvas) return;
    ctx = canvas.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    canvas.addEventListener('click', onCanvasClick);
    drawStatic();
}

function resizeCanvas() {
    if (!canvas) return;
    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
}

function drawStatic() {
    if (!ctx) return;
    ctx.fillStyle = '#fdf4ea';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

async function startGame() {
    const user = await apiCall('/api/user/');
    if (!user || user.coins < 5) {
        showToast(`Need 5 coins (you have ${user?.coins || 0})`);
        return;
    }
    
    const result = await apiCall('/api/game/play', 'POST', {});
    if (!result || !result.success) {
        showToast('Failed to start game');
        return;
    }
    
    gameActive = true;
    gameScore = 0;
    gameLives = 3;
    gameLevel = 1;
    bubbles = [];
    earnedThisGame = 0;
    spawnDelay = 1500;
    speed = 0.7;
    
    document.getElementById('startOverlay').classList.add('hidden');
    document.getElementById('gameoverOverlay').classList.add('hidden');
    document.getElementById('gameScore').innerText = '0';
    document.getElementById('gameLives').innerText = '3';
    document.getElementById('gameLevel').innerText = '1';
    
    resizeCanvas();
    lastSpawn = performance.now();
    gameLoop();
}

function spawnBubble() {
    if (!gameActive) return;
    const rad = 26 + Math.random() * 12;
    const special = Math.random() < 0.12;
    const colors = ['#f3b0b8', '#b5d8ff', '#c5e0d4', '#e3d0ff'];
    const color = special ? '#FFD966' : colors[Math.floor(Math.random() * colors.length)];
    
    bubbles.push({
        x: rad + Math.random() * (canvas.width - rad * 2),
        y: canvas.height + rad,
        r: rad,
        color: color,
        special: special,
        vy: speed + Math.random() * 0.3
    });
}

function gameLoop(now) {
    if (!gameActive) return;
    
    if (now - lastSpawn > spawnDelay) {
        spawnBubble();
        lastSpawn = now;
    }
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    for (let i = bubbles.length - 1; i >= 0; i--) {
        const b = bubbles[i];
        b.y -= b.vy;
        
        if (b.y + b.r < 0) {
            bubbles.splice(i, 1);
            gameLives--;
            document.getElementById('gameLives').innerText = gameLives;
            vibrate(60);
            playSound(320, 0.15);
            
            if (gameLives <= 0) {
                endGame();
                return;
            }
            continue;
        }
        
        // Draw bubble
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
        ctx.fillStyle = b.color;
        ctx.fill();
        ctx.strokeStyle = '#ad9a88';
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Highlight
        ctx.fillStyle = 'rgba(255,255,240,0.7)';
        ctx.beginPath();
        ctx.arc(b.x - 5, b.y - 5, b.r * 0.2, 0, Math.PI * 2);
        ctx.fill();
        
        // Icon
        ctx.fillStyle = '#333';
        ctx.font = `${b.r * 0.6}px monospace`;
        ctx.fillText(b.special ? '★' : '●', b.x - 7, b.y + 6);
    }
    
    animFrame = requestAnimationFrame(gameLoop);
}

function onCanvasClick(e) {
    if (!gameActive) return;
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const clickX = (e.clientX - rect.left) * scaleX;
    const clickY = (e.clientY - rect.top) * scaleY;
    
    for (let i = bubbles.length - 1; i >= 0; i--) {
        const b = bubbles[i];
        const dx = clickX - b.x;
        const dy = clickY - b.y;
        
        if (dx * dx + dy * dy <= b.r * b.r) {
            const points = b.special ? 12 : 5;
            gameScore += points;
            earnedThisGame += b.special ? 3 : 1;
            document.getElementById('gameScore').innerText = gameScore;
            playSound(770, 0.08);
            vibrate(30);
            bubbles.splice(i, 1);
            
            const newLevel = Math.floor(gameScore / 50) + 1;
            if (newLevel > gameLevel) {
                gameLevel = newLevel;
                spawnDelay = Math.max(600, 1600 - gameLevel * 90);
                speed = 0.7 + gameLevel * 0.12;
                document.getElementById('gameLevel').innerText = gameLevel;
                playSound(880, 0.2);
                vibrate([50, 50]);
            }
            break;
        }
    }
}

async function endGame() {
    gameActive = false;
    cancelAnimationFrame(animFrame);
    
    await apiCall('/api/game/reward', 'POST', { earned: earnedThisGame });
    await loadUserInfo();
    
    const best = localStorage.getItem('bestGameScore') || 0;
    if (gameScore > best) {
        localStorage.setItem('bestGameScore', gameScore);
        document.getElementById('gameBest').innerText = gameScore;
    }
    
    document.getElementById('finalScoreMsg').innerHTML = `Score: ${gameScore}`;
    document.getElementById('earnedCoinsMsg').innerHTML = `+${earnedThisGame} coins earned`;
    document.getElementById('gameoverOverlay').classList.remove('hidden');
    drawStatic();
}

function resetGame() {
    document.getElementById('gameoverOverlay').classList.add('hidden');
    document.getElementById('startOverlay').classList.remove('hidden');
    drawStatic();
}

// ========== UI HELPERS ==========
function setHeaderDate() {
    const d = new Date();
    const options = { weekday: 'short', month: 'short', day: 'numeric' };
    document.getElementById('headerDate').innerText = d.toLocaleDateString(undefined, options);
}

function buildDaysSelector() {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const container = document.getElementById('daysContainer');
    if (!container) return;
    
    container.innerHTML = days.map(d => `<div class="day-chip" data-day="${d}">${d}</div>`).join('');
    document.querySelectorAll('.day-chip').forEach(chip => {
        chip.addEventListener('click', () => chip.classList.toggle('selected'));
    });
}

function setPriority(p, element) {
    currentPriority = p;
    document.querySelectorAll('.priority-option').forEach(opt => opt.classList.remove('selected'));
    element.classList.add('selected');
}

function toggleAddForm(type) {
    const scheduleForm = document.getElementById('scheduleForm');
    const taskForm = document.getElementById('taskForm');
    const schedBtn = document.getElementById('showScheduleFormBtn');
    const taskBtn = document.getElementById('showTaskFormBtn');
    
    if (type === 'schedule') {
        scheduleForm.style.display = 'block';
        taskForm.style.display = 'none';
        if (schedBtn) schedBtn.style.background = 'var(--primary-soft)';
        if (taskBtn) taskBtn.style.background = 'transparent';
    } else {
        scheduleForm.style.display = 'none';
        taskForm.style.display = 'block';
        if (schedBtn) schedBtn.style.background = 'transparent';
        if (taskBtn) taskBtn.style.background = 'var(--primary-soft)';
    }
}

function switchView(view) {
    const views = ['dashboard', 'schedule', 'tasks', 'add', 'game'];
    views.forEach(v => {
        const el = document.getElementById(v + 'View');
        if (el) el.classList.remove('active');
    });
    
    const activeView = document.getElementById(view + 'View');
    if (activeView) activeView.classList.add('active');
    
    const tabs = document.querySelectorAll('.tab-btn');
    const viewMap = { dashboard: 0, schedule: 1, tasks: 2, add: 3, game: 4 };
    tabs.forEach((tab, i) => {
        if (i === viewMap[view]) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    if (view === 'dashboard') loadDashboard();
    if (view === 'schedule') loadSchedules();
    if (view === 'tasks') loadTasks();
    if (view === 'game') loadUserInfo();
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function showToast(message) {
    const toast = document.getElementById('toastMsg');
    const textSpan = document.getElementById('toastText');
    if (!toast || !textSpan) return;
    
    textSpan.innerText = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2800);
}

function showCelebration(message) {
    const modal = document.getElementById('celebModal');
    const msgSpan = document.getElementById('modalMsg');
    const rewardSpan = document.getElementById('modalReward');
    
    if (!modal) return;
    
    document.getElementById('modalTitle').innerText = 'Task Completed!';
    if (msgSpan) msgSpan.innerHTML = message;
    if (rewardSpan) rewardSpan.innerHTML = 'Great job! Keep going! 🎉';
    
    modal.classList.add('show');
    setTimeout(() => closeModal(), 3000);
}

function closeModal() {
    const modal = document.getElementById('celebModal');
    if (modal) modal.classList.remove('show');
}

function playSound(freq, dur, vol = 0.2) {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.frequency.value = freq;
        gain.gain.value = vol;
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + dur);
        osc.start();
        osc.stop(audioCtx.currentTime + dur);
        if (audioCtx.state === 'suspended') audioCtx.resume();
    } catch (e) {}
}

function vibrate(pattern) {
    if ('vibrate' in navigator) navigator.vibrate(pattern);
}

// Add these functions to your script.js

async function getAnalytics() {
    const tasks = await apiCall('/api/tasks/');
    if (!tasks) return;
    
    const completed = tasks.filter(t => t.done);
    const byPriority = {
        low: completed.filter(t => t.priority === 'low').length,
        med: completed.filter(t => t.priority === 'med').length,
        high: completed.filter(t => t.priority === 'high').length
    };
    
    // Find most productive time (simplified)
    const morning = completed.filter(t => t.due_time && parseInt(t.due_time) < 12).length;
    const afternoon = completed.filter(t => t.due_time && parseInt(t.due_time) >= 12 && parseInt(t.due_time) < 17).length;
    const evening = completed.filter(t => t.due_time && parseInt(t.due_time) >= 17).length;
    
    let bestTime = 'Morning';
    let bestCount = morning;
    if (afternoon > bestCount) { bestTime = 'Afternoon'; bestCount = afternoon; }
    if (evening > bestCount) { bestTime = 'Evening'; }
    
    document.getElementById('bestTimeDisplay').innerHTML = `📊 You're most productive during the <strong>${bestTime}</strong>!`;
    
    // Category breakdown
    const categories = {};
    completed.forEach(t => {
        categories[t.category] = (categories[t.category] || 0) + 1;
    });
    
    const categoryHtml = Object.entries(categories).map(([cat, count]) => 
        `<div class="category-item"><span>${cat}</span><span>${count} tasks</span><div class="category-bar" style="width: ${(count/completed.length)*100}%"></div></div>`
    ).join('');
    
    document.getElementById('categoryBreakdown').innerHTML = categoryHtml || '<p>Complete more tasks to see insights!</p>';
}

// Make functions global for HTML onclick
window.switchView = switchView;
window.setPriority = setPriority;
window.toggleAddForm = toggleAddForm;
window.addTask = addTask;
window.addSchedule = addSchedule;
window.toggleTask = toggleTask;
window.deleteTask = deleteTask;
window.deleteSchedule = deleteSchedule;
window.startGame = startGame;
window.resetGame = resetGame;
window.closeModal = closeModal;