import React, { useState, useEffect, useRef } from 'react';
import './AdminDashboard.css';

const AdminDashboard = () => {
    const [stats, setStats] = useState({});
    const [queueTasks, setQueueTasks] = useState([]);
    const [recentActivity, setRecentActivity] = useState([]);
    const [dispatchLocations, setDispatchLocations] = useState([]);
    const [serviceDistribution, setServiceDistribution] = useState({});
    const mapRef = useRef(null);
    const leafletMapRef = useRef(null);
    const markersRef = useRef([]);

    useEffect(() => {
        loadDashboardData();
        
        // Refresh data every 30 seconds
        const interval = setInterval(loadDashboardData, 30000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (dispatchLocations.length > 0) {
            initializeMap();
        }
    }, [dispatchLocations]);

    const loadDashboardData = async () => {
        try {
            const [statsRes, queueRes, activityRes, locationsRes, distributionRes] = await Promise.all([
                fetch('/api/v1/admin/stats', { credentials: 'include' }),
                fetch('/api/v1/admin/queue', { credentials: 'include' }),
                fetch('/api/v1/admin/activity', { credentials: 'include' }),
                fetch('/api/v1/admin/dispatch-locations', { credentials: 'include' }),
                fetch('/api/v1/admin/service-distribution', { credentials: 'include' })
            ]);

            if (statsRes.ok) setStats(await statsRes.json());
            if (queueRes.ok) setQueueTasks(await queueRes.json());
            if (activityRes.ok) setRecentActivity(await activityRes.json());
            if (locationsRes.ok) setDispatchLocations(await locationsRes.json());
            if (distributionRes.ok) setServiceDistribution(await distributionRes.json());
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    };

    const initializeMap = () => {
        if (!window.L || !mapRef.current) return;

        // Clear existing map
        if (leafletMapRef.current) {
            leafletMapRef.current.remove();
        }

        // Clear existing markers
        markersRef.current = [];

        // Create new map
        leafletMapRef.current = window.L.map(mapRef.current).setView([30.3753, 69.3451], 6);

        // Add tile layer
        window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(leafletMapRef.current);

        // Add dispatch markers
        dispatchLocations.forEach(location => {
            const marker = window.L.marker([location.latitude, location.longitude])
                .addTo(leafletMapRef.current);

            const serviceColors = {
                medical: '#ef4444',
                police: '#f59e0b', 
                disaster: '#dc2626',
                general: '#6b7280'
            };

            // Create flashing marker icon
            const color = serviceColors[location.service] || '#6b7280';
            const icon = window.L.divIcon({
                className: 'dispatch-marker',
                html: `<div class="marker-dot flashing" style="background-color: ${color}"></div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            marker.setIcon(icon);
            marker.bindPopup(`
                <div class="marker-popup">
                    <strong>${location.service.toUpperCase()}</strong><br>
                    User: ${location.user_name}<br>
                    Time: ${new Date(location.created_at).toLocaleString()}
                </div>
            `);

            markersRef.current.push(marker);
        });
    };

    const formatTimeAgo = (timestamp) => {
        const minutes = Math.floor((Date.now() - new Date(timestamp)) / 60000);
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    };

    const activityIcons = {
        medical: '🏥',
        police: '🚔',
        disaster: '🌪️',
        user: '👤',
        system: '⚙️'
    };

    return (
        <div className="admin-dashboard">
            <div className="dashboard-header">
                <h1>Admin Dashboard</h1>
                <button onClick={loadDashboardData} className="refresh-btn">
                    Refresh Data
                </button>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-value">{stats.total_users || 0}</div>
                    <div className="stat-label">Total Users</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{stats.active_tasks || 0}</div>
                    <div className="stat-label">Active Tasks</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{stats.resolved_today || 0}</div>
                    <div className="stat-label">Resolved Today</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{stats.total_events || 0}</div>
                    <div className="stat-label">Total Events</div>
                </div>
            </div>

            <div className="dashboard-content">
                {/* Dispatch Map */}
                <div className="dashboard-section map-section">
                    <h2>Live Dispatch Map</h2>
                    <div ref={mapRef} className="dispatch-map"></div>
                </div>

                {/* Active Queue */}
                <div className="dashboard-section">
                    <h2>Active Queue ({queueTasks.length})</h2>
                    <div className="queue-container">
                        {queueTasks.length === 0 ? (
                            <div className="empty-state">No active tasks in queue</div>
                        ) : (
                            queueTasks.map(task => (
                                <div key={task.id} className="queue-item">
                                    <div className="queue-header">
                                        <span className={`queue-service ${task.service}`}>
                                            {task.service.toUpperCase()}
                                        </span>
                                        <span className={`queue-priority priority-${task.priority}`}>
                                            P{task.priority}
                                        </span>
                                    </div>
                                    <div className="queue-time">
                                        {formatTimeAgo(task.created_at)} • {task.user_location}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="dashboard-section">
                    <h2>Recent Activity</h2>
                    <div className="activity-container">
                        {recentActivity.length === 0 ? (
                            <div className="empty-state">No recent activity</div>
                        ) : (
                            recentActivity.slice(0, 10).map((activity, index) => (
                                <div key={index} className="activity-item">
                                    <div className={`activity-icon ${activity.type}`}>
                                        {activityIcons[activity.type] || '📋'}
                                    </div>
                                    <div className="activity-content">
                                        <div className="activity-text">{activity.message}</div>
                                        <div className="activity-time">
                                            {formatTimeAgo(activity.timestamp)}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Service Distribution Chart */}
                <div className="dashboard-section">
                    <h2>Service Distribution</h2>
                    <div className="service-chart">
                        {['medical', 'police', 'disaster', 'general'].map(service => {
                            const count = serviceDistribution[service] || 0;
                            const maxValue = Math.max(...Object.values(serviceDistribution), 1);
                            const height = (count / maxValue * 80) + 20;
                            
                            return (
                                <div key={service} className="chart-bar" style={{ height: `${height}%` }}>
                                    <div className="chart-value">{count}</div>
                                    <div className="chart-label">{service}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;