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

    // Separate tasks (mock logic for now since backend might just return a flat list)
    // Assuming backend returns a list of task objects
    const currentTasks = tasks.filter(t => t.status === 'IN PROGRESS' || t.priority === 'urgent');
    const queueTasks = tasks.filter(t => t.status !== 'IN PROGRESS' && t.priority !== 'urgent');

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
                                    <div key={task.id} className={`task-card-large ${task.priority}`}>
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
                                            <button className="btn-blue full">Mark as Done</button>
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
                                    <div key={q.id} className="queue-card">
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
                                            <button className="outline-btn">Start Task</button>
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
