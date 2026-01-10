import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './CleanerDashboard.css';

const CleanerDashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [processingTask, setProcessingTask] = useState(null); // Track which task is being processed

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

    const refreshTasks = async () => {
        if (!user?.user_id) return;
        try {
            const data = await api.getTasks(user.user_id);
            setTasks(data || []);
        } catch (error) {
            console.error('Failed to refresh tasks', error);
        }
    };

    const handleAcceptTask = async (taskId) => {
        if (!user?.user_id) {
            alert('User not loaded. Please refresh the page.');
            return;
        }
        setProcessingTask(taskId);
        try {
            await api.acceptTask(taskId, user.user_id);
            alert('✅ Task accepted successfully!');
            await refreshTasks();
        } catch (error) {
            console.error('Failed to accept task', error);
            alert('❌ Error accepting task: ' + (error.message || 'Unknown error'));
        } finally {
            setProcessingTask(null);
        }
    };

    const handleCompleteTask = async (taskId) => {
        if (!user?.user_id) {
            alert('User not loaded. Please refresh the page.');
            return;
        }

        // Confirm before completing
        const confirmed = window.confirm(
            'Are you sure you want to mark this task as completed?\n\n' +
            'This will trigger the next step in the workflow.'
        );

        if (!confirmed) return;

        setProcessingTask(taskId);
        try {
            const result = await api.completeTask(taskId, user.user_id, 'Task completed');
            alert('✅ Task completed successfully!\n\n' + (result.message || 'The next workflow step has been triggered.'));
            await refreshTasks();
        } catch (error) {
            console.error('Failed to complete task', error);
            alert('❌ Error completing task: ' + (error.message || 'Unknown error'));
        } finally {
            setProcessingTask(null);
        }
    };

    // Filter tasks - show assigned/accepted tasks as active, completed tasks are hidden
    const activeTasks = tasks.filter(t => t.status === 'assigned' || t.status === 'accepted');
    const completedTasks = tasks.filter(t => t.status === 'completed');

    return (
        <div className="cleaner-dashboard-premium">
            <aside className="sidebar">
                <div className="sidebar-brand-top">
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
                        <button
                            className="icon-btn"
                            onClick={refreshTasks}
                            title="Refresh tasks"
                        >
                            🔄
                        </button>
                        <div className="search-bar">
                            <span>🔍</span>
                            <input type="text" placeholder="Search tasks or rooms..." />
                        </div>
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
                                    <div key={task.task_id} className={`task-card-v2 ${task.priority || 'normal'}`}>
                                        <div className="priority-line"></div>
                                        <div className="card-top">
                                            <div className="meta">
                                                <span className="prio-label">{task.status?.toUpperCase() || 'ASSIGNED'}</span>
                                                <h4>Bed {task.bed_id || '-'} • Patient {task.patient_id?.substring(0, 8) || 'N/A'}</h4>
                                                <p className="task-type-sub">{task.type === 'cleaning' ? 'Bed Preparation Cleaning' : task.type || 'General Cleaning'}</p>
                                            </div>
                                            <div className="time-info">
                                                <span className="assigned">
                                                    {task.created_at
                                                        ? (() => {
                                                            // Handle Firestore timestamp format
                                                            const date = task.created_at.seconds
                                                                ? new Date(task.created_at.seconds * 1000)
                                                                : task.created_at._seconds
                                                                    ? new Date(task.created_at._seconds * 1000)
                                                                    : new Date(task.created_at);
                                                            return date.toLocaleDateString();
                                                        })()
                                                        : 'Today'}
                                                </span>
                                                <span className="elapsed">{task.status === 'accepted' ? 'Accepted' : 'Awaiting Acceptance'}</span>
                                            </div>
                                        </div>

                                        <div className="card-body">
                                            <div className="tag-row">
                                                <span className="safety-pill">🛡️ PPE Required</span>
                                                {task.type === 'cleaning' && <span className="warning-pill">🧹 Bed Preparation</span>}
                                            </div>
                                        </div>

                                        <div className="card-actions">
                                            {task.status === 'assigned' ? (
                                                <button
                                                    className="btn-accept"
                                                    onClick={() => handleAcceptTask(task.task_id)}
                                                    disabled={processingTask === task.task_id}
                                                >
                                                    {processingTask === task.task_id ? 'Processing...' : 'Accept Task'}
                                                </button>
                                            ) : task.status === 'accepted' ? (
                                                <button
                                                    className="btn-done-green"
                                                    onClick={() => handleCompleteTask(task.task_id)}
                                                    disabled={processingTask === task.task_id}
                                                >
                                                    {processingTask === task.task_id ? 'Processing...' : 'Mark Completed'}
                                                </button>
                                            ) : (
                                                <button className="btn-done-green" disabled>
                                                    {task.status === 'completed' ? 'Completed' : task.status}
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>

                    <aside className="column-pool">
                        <div className="column-header">
                            <h3>Completed Tasks</h3>
                            <span className="count-badge">{completedTasks.length} Completed</span>
                        </div>

                        {loading ? (
                            <div className="loading-state">Loading history...</div>
                        ) : completedTasks.length === 0 ? (
                            <div className="empty-state">No completed tasks yet.</div>
                        ) : (
                            <div className="pool-stack">
                                {completedTasks.slice(0, 10).map(task => (
                                    <div key={task.task_id} className="pool-item-card">
                                        <div className="p-top">
                                            <span className="p-prio-pill completed">COMPLETED</span>
                                            <span className="p-time">
                                                {task.completed_at
                                                    ? (() => {
                                                        // Handle Firestore timestamp format
                                                        const date = task.completed_at.seconds
                                                            ? new Date(task.completed_at.seconds * 1000)
                                                            : task.completed_at._seconds
                                                                ? new Date(task.completed_at._seconds * 1000)
                                                                : new Date(task.completed_at);
                                                        return date.toLocaleDateString();
                                                    })()
                                                    : 'Recently'}
                                            </span>
                                        </div>
                                        <div className="p-middle">
                                            <h5>Bed {task.bed_id || '-'}</h5>
                                            <p>{task.type === 'cleaning' ? 'Bed Preparation' : task.type || 'Standard Clean'}</p>
                                            {task.notes && <small>{task.notes}</small>}
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
