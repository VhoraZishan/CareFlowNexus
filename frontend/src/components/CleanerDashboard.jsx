import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './CleanerDashboard.css';

const CleanerDashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [tasks, setTasks] = useState([
        { id: 1, room: '402', bed: 'B', type: 'Discharge Turnover', priority: 'high', assignedAt: '10:15 AM', status: 'IN PROGRESS' },
        { id: 2, room: '415', bed: 'A', type: 'Routine Daily Clean', priority: 'normal', assignedAt: '10:30 AM', status: 'IN PROGRESS' },
        { id: 3, room: '422', bed: 'B', type: 'Terminal Clean', priority: 'low', assignedAt: '11:00 AM', status: 'PENDING' }
    ]);
    const [pool, setPool] = useState([
        { id: 4, room: '305', type: 'Stat Turnover Requested', priority: 'medium', time: '11:15 AM' },
        { id: 5, room: '310', type: 'Discharge Turnover', priority: 'low', time: '12:00 PM' }
    ]);

    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (!userStr) { navigate('/'); return; }
        setUser(JSON.parse(userStr));
    }, [navigate]);

    return (
        <div className="cleaner-dashboard-premium">
            <aside className="sidebar-premium">
                <div className="sidebar-logo">
                    <h1>CareFlow Nexus</h1>
                    <p>CLEANING SERVICES</p>
                </div>

                <nav className="sidebar-nav">
                    <button className="nav-btn active">Cleaning Dashboard</button>
                    <button className="nav-btn">My History</button>
                </nav>

                <div className="sidebar-footer">
                    <div className="user-profile-widget">
                        <div className="user-avatar-small">
                            <img src={`https://ui-avatars.com/api/?name=Staff+Member&background=f97316&color=fff&bold=true`} alt="Avatar" />
                        </div>
                        <div className="user-meta-small">
                            <h4>Staff Member</h4>
                            <p>Shift ends 07:00 PM</p>
                        </div>
                        <button className="logout-icon-btn" onClick={() => { localStorage.removeItem('user'); navigate('/'); }}>
                            🚪
                        </button>
                    </div>
                </div>
            </aside>

            <main className="cleaner-main">
                <header className="cleaner-header">
                    <div className="header-left">
                        <h2>Cleaning Services Task Management <span className="status-badge">ON SHIFT</span></h2>
                    </div>

                    <div className="header-right">
                        <div className="search-bar">
                            <span>🔍</span>
                            <input type="text" placeholder="Search tasks or rooms..." />
                        </div>
                        <button className="icon-btn">🔔</button>
                    </div>
                </header>

                <div className="cleaner-content-grid">
                    <section className="column-tasks">
                        <div className="column-header">
                            <h3>Cleaning Tasks Queue</h3>
                            <span className="count-badge">3 Active Assignments</span>
                        </div>

                        <div className="task-stack">
                            {tasks.map(task => (
                                <div key={task.id} className={`task-card-v2 ${task.priority}`}>
                                    <div className="priority-line"></div>
                                    <div className="card-top">
                                        <div className="meta">
                                            <span className="prio-label">{task.priority.toUpperCase()} PRIORITY</span>
                                            <h4>Room {task.room} • Bed {task.bed}</h4>
                                            <p className="task-type-sub">{task.type}</p>
                                        </div>
                                        <div className="time-info">
                                            <span className="assigned">Assigned {task.assignedAt}</span>
                                            <span className="elapsed">Elapsed: 12m</span>
                                        </div>
                                    </div>

                                    <div className="card-body">
                                        <div className="tag-row">
                                            {task.priority === 'high' && <span className="warning-pill">⚠️ Isolation Required</span>}
                                            <span className="safety-pill">🛡️ PPE Required</span>
                                            {task.priority === 'normal' && <span className="safety-pill">✅ Standard Precautions</span>}
                                        </div>
                                    </div>

                                    <div className="card-actions">
                                        <button className="btn-done-green">Mark Completed</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    <aside className="column-pool">
                        <div className="column-header">
                            <h3>Available Pool</h3>
                            <button className="filter-btn">≡</button>
                        </div>

                        <div className="pool-stack">
                            {pool.map(item => (
                                <div key={item.id} className="pool-item-card">
                                    <div className="p-top">
                                        <span className={`p-prio-pill ${item.priority}`}>{item.priority.toUpperCase()}</span>
                                        <span className="p-time">{item.time}</span>
                                    </div>
                                    <div className="p-middle">
                                        <h5>Room {item.room}</h5>
                                        <p>{item.type}</p>
                                    </div>
                                    <div className="p-bottom">
                                        <button className="link-btn">View Details</button>
                                        <button className="accept-btn">Accept Task</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </aside>
                </div>
            </main>
        </div>
    );
};

export default CleanerDashboard;
