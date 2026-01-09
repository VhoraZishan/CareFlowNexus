import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './CleanerDashboard.css';

const CleanerDashboard = () => {
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

                // Fetch real tasks
                const data = await api.getTasks(parsedUser.user_id);
                setTasks(data || []);
            } catch (err) {
                console.error("Failed to load cleaner tasks", err);
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

    // Filter tasks
    const activeTasks = tasks.filter(t => t.status === 'IN PROGRESS' || t.priority === 'high');
    const poolTasks = tasks.filter(t => t.status !== 'IN PROGRESS' && t.priority !== 'high');

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
                    <button className="nav-btn" onClick={handleLogout}>Logout</button>
                </nav>

                <div className="sidebar-footer">
                    <div className="user-profile-widget">
                        <div className="user-avatar-small">
                            <img src={`https://ui-avatars.com/api/?name=${user?.name || user?.user_id || 'Staff'}&background=f97316&color=fff&bold=true`} alt="Avatar" />
                        </div>
                        <div className="user-meta-small">
                            <h4>{user?.name || user?.user_id}</h4>
                            <p>Shift ends 07:00 PM</p>
                        </div>
                        <button className="logout-icon-btn" onClick={handleLogout} title="Logout">
                            ⏻
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
                            <span className="count-badge">{activeTasks.length} Active Assignments</span>
                        </div>

                        {loading ? (
                            <div className="loading-state">Syncing cleaning schedule...</div>
                        ) : activeTasks.length === 0 ? (
                            <div className="empty-state">No active cleaning tasks assigned.</div>
                        ) : (
                            <div className="task-stack">
                                {activeTasks.map(task => (
                                    <div key={task.id} className={`task-card-v2 ${task.priority}`}>
                                        <div className="priority-line"></div>
                                        <div className="card-top">
                                            <div className="meta">
                                                <span className="prio-label">{task.priority?.toUpperCase() || 'NORMAL'} PRIORITY</span>
                                                <h4>Room {task.room || 'TBD'} • Bed {task.bed || '-'}</h4>
                                                <p className="task-type-sub">{task.type || 'General Cleaning'}</p>
                                            </div>
                                            <div className="time-info">
                                                <span className="assigned">Assigned {task.assignedAt || 'Today'}</span>
                                                <span className="elapsed">In Progress</span>
                                            </div>
                                        </div>

                                        <div className="card-body">
                                            <div className="tag-row">
                                                {task.priority === 'high' && <span className="warning-pill">⚠️ Isolation Required</span>}
                                                <span className="safety-pill">🛡️ PPE Required</span>
                                            </div>
                                        </div>

                                        <div className="card-actions">
                                            <button className="btn-done-green">Mark Completed</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>

                    <aside className="column-pool">
                        <div className="column-header">
                            <h3>Available Pool</h3>
                            <button className="filter-btn">≡</button>
                        </div>

                        {loading ? (
                            <div className="loading-state">Loading pool...</div>
                        ) : poolTasks.length === 0 ? (
                            <div className="empty-state">Pool is empty.</div>
                        ) : (
                            <div className="pool-stack">
                                {poolTasks.map(item => (
                                    <div key={item.id} className="pool-item-card">
                                        <div className="p-top">
                                            <span className={`p-prio-pill ${item.priority || 'normal'}`}>{item.priority?.toUpperCase() || 'NORMAL'}</span>
                                            <span className="p-time">{item.time || 'Pending'}</span>
                                        </div>
                                        <div className="p-middle">
                                            <h5>Room {item.room || '-'}</h5>
                                            <p>{item.type || 'Standard Clean'}</p>
                                        </div>
                                        <div className="p-bottom">
                                            <button className="link-btn">View Details</button>
                                            <button className="accept-btn">Accept Task</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </aside>
                </div>
            </main>
        </div>
    );
};

export default CleanerDashboard;
