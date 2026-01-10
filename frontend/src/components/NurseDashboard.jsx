import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './NurseDashboard.css';

const NurseDashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                const userStr = localStorage.getItem('user');
                if (!userStr) {
                    navigate('/');
                    return;
                }
                const parsedUser = JSON.parse(userStr);
                setUser(parsedUser);

                // DEBUG LOGGING
                console.log(`[NurseDashboard] Fetching tasks for user ID: ${parsedUser.user_id}`);
                console.log(`[NurseDashboard] User Role: ${parsedUser.role}`);

                // Fetch real tasks
                const data = await api.getTasks(parsedUser.user_id);
                console.log('[NurseDashboard] Tasks response:', data);
                setTasks(data || []);
            } catch (err) {
                console.error("Failed to load tasks", err);
                alert(`Error loading tasks: ${err.message}\nCheck console for details.`);
            } finally {
                setLoading(false);
            }
        };

        fetchTasks();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem('user');
        navigate('/');
    };

    // Separate tasks
    // Backend returns 'assigned' for queue and 'accepted' for current tasks (based on backend logic inspection)
    // or 'IN PROGRESS' if that's what backend returns?
    // Let's check backend: accept_task sets status to "accepted". complete_task sets "completed".
    // So Queue = "assigned", Current = "accepted".

    // Filter logic adjustment based on backend
    const currentTasks = tasks.filter(t => t.status === 'accepted' || t.status === 'IN PROGRESS');
    const queueTasks = tasks.filter(t => t.status === 'assigned');

    const handleAcceptTask = async (taskId) => {
        if (!user) return;
        try {
            await api.acceptTask(taskId, user.user_id);
            // Refresh
            const data = await api.getTasks(user.user_id);
            setTasks(data || []);
        } catch (err) {
            console.error("Failed to accept task", err);
            alert("Failed to start task: " + err.message);
        }
    };

    const handleCompleteTask = async (taskId) => {
        if (!user) return;
        try {
            const notes = prompt("Enter completion notes (optional):") || "";
            await api.completeTask(taskId, user.user_id, notes);
            // Refresh
            const data = await api.getTasks(user.user_id);
            setTasks(data || []);
        } catch (err) {
            console.error("Failed to complete task", err);
            alert("Failed to complete task: " + err.message);
        }
    };

    return (
        <div className="nurse-layout-premium">
            <aside className="nurse-sidebar">
                <div className="sidebar-brand">
                    <h1>CareFlow Nexus</h1>
                    <p>NURSING UNIT A</p>
                </div>

                <nav className="nurse-nav">
                    <button className="n-nav-btn active">
                        <span className="icon">⊞</span> Task Dashboard
                    </button>
                    <button className="n-nav-btn">
                        <span className="icon">👥</span> My Patients
                    </button>
                    <button className="n-nav-btn" onClick={handleLogout}>
                        <span className="icon"></span> Logout
                    </button>
                </nav>

                <div className="sidebar-bottom-profile">
                    <div className="profile-card">
                        <div className="avatar">
                            <img src={`https://ui-avatars.com/api/?name=${user?.name || user?.user_id || 'Nurse'}&background=10b981&color=fff&bold=true`} alt="Nurse" />
                        </div>
                        <div className="meta">
                            <h4>{user?.name || user?.user_id}</h4>
                            <p>Shift ends 07:00 PM</p>
                        </div>
                        <button className="logout-btn" onClick={handleLogout} title="Logout">
                            ⏻
                        </button>
                    </div>
                </div>
            </aside>

            <main className="nurse-content">
                <header className="nurse-header">
                    <div className="header-left">
                        <h2>Nurse Task Management</h2>
                        <span className="shift-badge">ON SHIFT</span>
                    </div>
                    <div className="header-right">
                        <div className="search-pill">
                            <span>🔍</span>
                            <input type="text" placeholder="Search patients or tasks..." />
                        </div>
                        <button className="icon-btn">🔔</button>
                        <button className="icon-btn">💬</button>
                    </div>
                </header>

                <div className="dashboard-columns">
                    {/* Left Column: Current Tasks */}
                    <div className="col-current">
                        <div className="col-header">
                            <h3>Current Tasks</h3>
                            <span className="count-tag">{currentTasks.length} Active</span>
                        </div>

                        {loading ? (
                            <div className="loading-state">Syncing tasks...</div>
                        ) : currentTasks.length === 0 ? (
                            <div className="empty-state">No urgent tasks at the moment.</div>
                        ) : (
                            <div className="task-stack-main">
                                {currentTasks.map(task => (
                                    <div key={task.task_id} className={`task-card-large ${task.priority || 'normal'}`}>
                                        <div className="card-top-row">
                                            <div className="priority-text">
                                                {task.priority?.toUpperCase() || 'NORMAL'} PRIORITY
                                            </div>
                                            <div className="time-text">
                                                <strong>Due {task.due || 'ASAP'}</strong>
                                                <span className="sub-time">Current: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                        </div>

                                        <div className="patient-header">
                                            <h3>{task.patient_name || 'Unknown Patient'} <span className="divider">|</span> Room {task.room || 'TBD'}</h3>
                                        </div>

                                        <div className="task-detail-box">
                                            <div className="icon-box">
                                                {(task.type || '').includes('Vital') ? '📈' : '💊'}
                                            </div>
                                            <div className="detail-text">
                                                <h5>{task.type || 'General Task'}</h5>
                                                <p>{task.details || 'No additional details provided.'}</p>
                                            </div>
                                            <div className="status-pill-right">
                                                {task.status === 'IN PROGRESS' ? '◉ IN PROGRESS' : '🕒 READY'}
                                            </div>
                                        </div>

                                        <div className="action-row">
                                            <button className="btn-blue full" onClick={() => handleCompleteTask(task.task_id)}>Mark as Done</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Right Column: Queue */}
                    <div className="col-queue">
                        <div className="col-header">
                            <h3>Upcoming Queue</h3>
                            <button className="filter-icon">≡</button>
                        </div>

                        {loading ? (
                            <div className="loading-state">Loading queue...</div>
                        ) : queueTasks.length === 0 ? (
                            <div className="empty-state">Queue is empty.</div>
                        ) : (
                            <div className="queue-list">
                                {queueTasks.map(q => (
                                    <div key={q.task_id} className="queue-card">
                                        <div className="q-top">
                                            <span className={`q-tag ${q.priority || 'normal'}`}>{q.priority?.toUpperCase() || 'NORMAL'}</span>
                                            <div className="q-time">
                                                <strong>{q.due || 'Today'}</strong>
                                                <span>LATER</span>
                                            </div>
                                        </div>
                                        <div className="q-main">
                                            <h4>{q.patient_name || 'Unknown'}</h4>
                                            <p>Room {q.room || '-'} • {q.type || 'Task'}</p>
                                        </div>
                                        <div className="q-actions">
                                            <button className="link-text">Review Notes</button>
                                            <button className="outline-btn" onClick={() => handleAcceptTask(q.task_id)}>Start Task</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default NurseDashboard;
