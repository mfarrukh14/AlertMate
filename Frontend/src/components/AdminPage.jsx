import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { adminService } from '../services/api';

const AdminPage = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState({
    active_emergencies: 0,
    total_users: 0,
    tasks_completed: 0,
    average_response_time: 0
  });
  const [queue, setQueue] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load all dashboard data
      const [statsResponse, queueResponse, activityResponse] = await Promise.allSettled([
        adminService.getStats(),
        adminService.getQueue(),
        adminService.getActivity()
      ]);

      // Handle stats
      if (statsResponse.status === 'fulfilled') {
        setStats(statsResponse.value.data);
      } else {
        // Mock data for demo
        setStats({
          active_emergencies: Math.floor(Math.random() * 20) + 5,
          total_users: Math.floor(Math.random() * 1000) + 500,
          tasks_completed: Math.floor(Math.random() * 100) + 250,
          average_response_time: (Math.random() * 30 + 15).toFixed(1)
        });
      }

      // Handle queue
      if (queueResponse.status === 'fulfilled') {
        setQueue(queueResponse.value.data);
      } else {
        // Mock data for demo
        setQueue([
          {
            id: 1,
            service: 'medical',
            priority: 3,
            created_at: new Date(Date.now() - 5 * 60000).toISOString(),
            user_location: 'Karachi, PK'
          },
          {
            id: 2,
            service: 'police',
            priority: 2,
            created_at: new Date(Date.now() - 12 * 60000).toISOString(),
            user_location: 'Lahore, PK'
          }
        ]);
      }

      // Handle activity
      if (activityResponse.status === 'fulfilled') {
        setActivity(activityResponse.value.data);
      } else {
        // Mock data for demo
        setActivity([
          {
            type: 'medical',
            message: 'Medical emergency resolved in Karachi',
            timestamp: new Date(Date.now() - 3 * 60000).toISOString()
          },
          {
            type: 'user',
            message: 'New user registered: Ahmad Ali',
            timestamp: new Date(Date.now() - 8 * 60000).toISOString()
          },
          {
            type: 'police',
            message: 'Police assistance dispatched to Lahore',
            timestamp: new Date(Date.now() - 15 * 60000).toISOString()
          }
        ]);
      }

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshDashboard = async () => {
    setLoading(true);
    await loadDashboardData();
  };

  const getTimeAgo = (timestamp) => {
    const minutes = Math.floor((Date.now() - new Date(timestamp)) / 60000);
    return minutes;
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 1: return 'bg-green-500/20 text-green-400';
      case 2: return 'bg-yellow-500/20 text-yellow-400';
      case 3: return 'bg-red-500/20 text-red-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  const getServiceColor = (service) => {
    switch (service) {
      case 'medical': return 'text-red-400';
      case 'police': return 'text-blue-400';
      case 'disaster': return 'text-yellow-400';
      default: return 'text-slate-400';
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'medical': return '🏥';
      case 'police': return '🚔';
      case 'disaster': return '🌪️';
      case 'user': return '👤';
      default: return '📋';
    }
  };

  if (loading && queue.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-700 to-purple-600 text-white p-6 shadow-lg">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            📊 AlertMate Admin
          </h1>
          <div className="flex items-center gap-4">
            <button
              onClick={refreshDashboard}
              disabled={loading}
              className="bg-white/20 hover:bg-white/30 border border-white/30 px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                  Refreshing...
                </>
              ) : (
                <>
                  🔄 Refresh
                </>
              )}
            </button>
            <button
              onClick={logout}
              className="bg-white/20 hover:bg-white/30 border border-white/30 px-4 py-2 rounded-lg text-sm font-medium transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 p-8 space-y-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-slate-400 text-sm font-semibold mb-2 uppercase tracking-wide">
              Active Emergencies
            </h3>
            <div className="text-3xl font-bold text-red-400 mb-2">{stats.active_emergencies}</div>
            <div className="text-sm text-slate-500">Currently active</div>
          </div>

          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-slate-400 text-sm font-semibold mb-2 uppercase tracking-wide">
              Total Users
            </h3>
            <div className="text-3xl font-bold text-green-400 mb-2">{stats.total_users}</div>
            <div className="text-sm text-slate-500">Registered users</div>
          </div>

          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-slate-400 text-sm font-semibold mb-2 uppercase tracking-wide">
              Tasks Completed
            </h3>
            <div className="text-3xl font-bold text-blue-400 mb-2">{stats.tasks_completed}</div>
            <div className="text-sm text-slate-500">This month</div>
          </div>

          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-6 shadow-2xl">
            <h3 className="text-slate-400 text-sm font-semibold mb-2 uppercase tracking-wide">
              Response Time
            </h3>
            <div className="text-3xl font-bold text-yellow-400 mb-2">{stats.average_response_time}s</div>
            <div className="text-sm text-slate-500">Average response</div>
          </div>
        </div>

        {/* Dashboard Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Active Queue */}
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-6 shadow-2xl">
            <h2 className="text-xl font-semibold text-blue-400 mb-4">🚨 Active Queue</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {queue.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No active tasks in queue
                </div>
              ) : (
                queue.map((task) => (
                  <div key={task.id} className="bg-slate-800/80 border border-slate-600/20 rounded-xl p-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className={`font-semibold text-sm uppercase tracking-wide ${getServiceColor(task.service)}`}>
                        {task.service}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${getPriorityColor(task.priority)}`}>
                        P{task.priority}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      {getTimeAgo(task.created_at)} minutes ago • {task.user_location}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-6 shadow-2xl">
            <h2 className="text-xl font-semibold text-blue-400 mb-4">📈 Recent Activity</h2>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {activity.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No recent activity
                </div>
              ) : (
                activity.map((item, index) => (
                  <div key={index} className="flex items-center gap-4 py-3 border-b border-slate-700/50 last:border-b-0">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${getServiceColor(item.type)} bg-current bg-opacity-20`}>
                      {getActivityIcon(item.type)}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm text-slate-200">{item.message}</div>
                      <div className="text-xs text-slate-400">
                        {getTimeAgo(item.timestamp)} minutes ago
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Service Distribution Chart */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-6 shadow-2xl">
          <h2 className="text-xl font-semibold text-blue-400 mb-4">📊 Service Distribution (Last 24h)</h2>
          <div className="flex items-end justify-around gap-4 h-48 bg-slate-900/60 rounded-xl p-4">
            <div className="flex flex-col items-center">
              <div className="w-12 bg-gradient-to-t from-red-600 to-red-400 rounded-t hover:from-red-500 hover:to-red-300 transition-all duration-300" style={{height: '60%'}} />
              <div className="text-xs font-semibold text-slate-300 mt-2">12</div>
              <div className="text-xs text-slate-500">Medical</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-12 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t hover:from-blue-500 hover:to-blue-300 transition-all duration-300" style={{height: '40%'}} />
              <div className="text-xs font-semibold text-slate-300 mt-2">8</div>
              <div className="text-xs text-slate-500">Police</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-12 bg-gradient-to-t from-yellow-600 to-yellow-400 rounded-t hover:from-yellow-500 hover:to-yellow-300 transition-all duration-300" style={{height: '20%'}} />
              <div className="text-xs font-semibold text-slate-300 mt-2">4</div>
              <div className="text-xs text-slate-500">Fire</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-12 bg-gradient-to-t from-purple-600 to-purple-400 rounded-t hover:from-purple-500 hover:to-purple-300 transition-all duration-300" style={{height: '15%'}} />
              <div className="text-xs font-semibold text-slate-300 mt-2">3</div>
              <div className="text-xs text-slate-500">Disaster</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;