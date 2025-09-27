import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { chatService } from '../services/api';

const ChatPage = () => {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add initial connection message
    addMessage('Connected to AlertMate Emergency Services', 'system', new Date());
  }, []);

  const addMessage = (content, type = 'agent', timestamp = new Date()) => {
    const newMessage = {
      id: Date.now() + Math.random(),
      content,
      type,
      timestamp,
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const quickMessage = (text) => {
    setInputMessage(text);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setLoading(true);

    // Add user message to chat
    addMessage(userMessage, 'user');

    try {
      const response = await chatService.sendMessage({
        userid: user.user_id,
        user_query: userMessage,
        user_location: `${user.lat}, ${user.lon}`,
        lat: user.lat,
        lon: user.lon,
        lang: 'en'
      });

      if (response.data) {
        addMessage(response.data.reply, 'agent');
      }
    } catch (error) {
      console.error('Chat error:', error);
      addMessage(
        error.response?.data?.detail || 'Network error. Please try again or call emergency hotlines.',
        'system'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-700 to-cyan-600 text-white p-6 shadow-lg">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            🚨 AlertMate
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-slate-100">Welcome, {user?.name}</span>
            <button
              onClick={logout}
              className="bg-white/20 hover:bg-white/30 border border-white/30 px-4 py-2 rounded-lg text-sm font-medium transition-all"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-8 p-8 max-h-[calc(100vh-120px)]">
        {/* Chat Section */}
        <div className="lg:col-span-2">
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-6 h-full flex flex-col shadow-2xl">
            {/* Emergency Notice */}
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 text-center">
              <strong className="text-red-400">🚨 Emergency Chat Active</strong>
              <br />
              <span className="text-red-300/80">Describe your emergency clearly. Help is on the way.</span>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto mb-6 space-y-4 pr-2">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-4 rounded-2xl border ${
                      message.type === 'user'
                        ? 'bg-blue-500/20 border-blue-500/35 text-blue-100'
                        : message.type === 'system'
                        ? 'bg-yellow-500/20 border-yellow-500/35 text-yellow-100 text-center'
                        : 'bg-slate-800/80 border-slate-600/30 text-slate-200'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div className="text-xs opacity-60 mt-2">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-slate-800/80 border border-slate-600/30 rounded-2xl p-4 text-slate-200">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-blue-500"></div>
                      AlertMate is responding...
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Section */}
            <div className="flex gap-4">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe your emergency situation in detail. Include location details if different from your registered address... (You can write in English, Urdu, or Roman Urdu)"
                className="flex-1 min-h-[100px] px-4 py-3 rounded-xl border border-slate-600/35 bg-slate-900/60 text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:ring-3 focus:ring-red-500/25 focus:border-red-500"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !inputMessage.trim()}
                className="px-6 py-3 bg-gradient-to-r from-red-600 to-red-500 text-white rounded-xl font-semibold hover:from-red-700 hover:to-red-600 focus:outline-none focus:ring-3 focus:ring-red-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 whitespace-nowrap self-start"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
                    Sending...
                  </div>
                ) : (
                  '🚨 Send Alert'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Info Sidebar */}
        <div className="space-y-6">
          {/* Location Info */}
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-4 shadow-xl">
            <h3 className="text-blue-400 font-semibold mb-2 flex items-center gap-2">
              📍 Your Location
            </h3>
            <p className="text-slate-300 text-sm">
              {user?.lat && user?.lon 
                ? `Lat: ${user.lat.toFixed(4)}, Lon: ${user.lon.toFixed(4)}`
                : 'Location not available'
              }
            </p>
          </div>

          {/* Available Services */}
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-4 shadow-xl">
            <h3 className="text-blue-400 font-semibold mb-2 flex items-center gap-2">
              🏥 Available Services
            </h3>
            <p className="text-slate-300 text-sm">
              Medical emergencies, Police assistance, Fire & rescue, Natural disasters
            </p>
          </div>

          {/* Quick Actions */}
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-4 shadow-xl">
            <h3 className="text-blue-400 font-semibold mb-3 flex items-center gap-2">
              ⚡ Quick Actions
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => quickMessage('Medical emergency / ایمرجنسی')}
                className="bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 text-blue-400 py-3 px-2 rounded-lg text-xs font-medium transition-all text-center"
              >
                🏥 Medical
              </button>
              <button
                onClick={() => quickMessage('Police needed / پولیس چاہیے')}
                className="bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 text-blue-400 py-3 px-2 rounded-lg text-xs font-medium transition-all text-center"
              >
                🚔 Police
              </button>
              <button
                onClick={() => quickMessage('Fire emergency / آگ لگ گئی')}
                className="bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 text-blue-400 py-3 px-2 rounded-lg text-xs font-medium transition-all text-center"
              >
                🔥 Fire
              </button>
              <button
                onClick={() => quickMessage('Natural disaster / قدرتی آفت')}
                className="bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 text-blue-400 py-3 px-2 rounded-lg text-xs font-medium transition-all text-center"
              >
                🌪️ Disaster
              </button>
            </div>
          </div>

          {/* Emergency Hotlines */}
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-600/25 rounded-2xl p-4 shadow-xl">
            <h3 className="text-blue-400 font-semibold mb-2 flex items-center gap-2">
              📞 Emergency Hotlines
            </h3>
            <div className="text-slate-300 text-sm space-y-1">
              <div>Police: <span className="font-mono">15</span></div>
              <div>Fire: <span className="font-mono">16</span></div>
              <div>Medical: <span className="font-mono">1122</span></div>
              <div>Rescue: <span className="font-mono">1021</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;