import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import { Calendar, ChevronLeft, ChevronRight, Clock, Film, Tv, Gamepad2, Loader2 } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [scheduleData, setScheduleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentTime, setCurrentTime] = useState(new Date());
  const [error, setError] = useState(null);
  const scrollContainerRef = useRef(null);

  // Format date for API
  const formatDate = (date) => {
    return date.toISOString().split('T')[0];
  };

  // Parse time to 24-hour format for sorting and current time line
  const parseTime = useCallback((timeStr) => {
    const match = timeStr.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
    if (!match) return 0;
    
    let hours = parseInt(match[1]);
    const minutes = parseInt(match[2]);
    const ampm = match[3].toUpperCase();
    
    if (ampm === 'AM' && hours === 12) hours = 0;
    if (ampm === 'PM' && hours !== 12) hours += 12;
    
    return hours * 60 + minutes;
  }, []);

  // Convert minutes since midnight to pixels (assuming 1 hour = 120px)
  const timeToPixels = useCallback((minutes) => {
    return (minutes / 60) * 120;
  }, []);

  // Get current time in minutes since midnight (ET)
  const getCurrentTimeMinutes = useCallback(() => {
    const now = new Date();
    // Convert to ET
    const etTime = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
    return etTime.getHours() * 60 + etTime.getMinutes();
  }, []);

  // Fetch schedule data
  const fetchSchedule = useCallback(async (date) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API}/schedule?date=${formatDate(date)}`);
      setScheduleData(response.data);
    } catch (err) {
      console.error('Error fetching schedule:', err);
      setError('Failed to load TV schedule. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Update current time every minute
  useEffect(() => {
    const updateTime = () => {
      setCurrentTime(new Date());
    };

    updateTime(); // Initial update
    const interval = setInterval(updateTime, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  // Fetch initial data
  useEffect(() => {
    fetchSchedule(currentDate);
  }, [currentDate, fetchSchedule]);

  // Auto-refresh every 15 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchSchedule(currentDate);
    }, 15 * 60 * 1000); // 15 minutes

    return () => clearInterval(interval);
  }, [currentDate, fetchSchedule]);

  // Handle date navigation
  const changeDate = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + direction);
    setCurrentDate(newDate);
  };

  // Handle show click
  const handleShowClick = (show) => {
    const searchQuery = encodeURIComponent(show.title);
    window.open(`https://www.google.com/search?q=${searchQuery}`, '_blank');
  };

  // Get show type icon
  const getShowTypeIcon = (type) => {
    if (type.toLowerCase().includes('film')) return <Film className="w-3 h-3" />;
    if (type.toLowerCase().includes('sports')) return <Gamepad2 className="w-3 h-3" />;
    return <Tv className="w-3 h-3" />;
  };

  // Format date for display
  const formatDisplayDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  // Get current time position for the time indicator line
  const getCurrentTimePosition = useCallback(() => {
    const currentMinutes = getCurrentTimeMinutes();
    return timeToPixels(currentMinutes);
  }, [getCurrentTimeMinutes, timeToPixels]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center">
        <div className="text-center text-white">
          <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin" />
          <p className="text-xl font-semibold">Loading TV Schedule...</p>
          <p className="text-gray-400 mt-2">Fetching real-time programming data</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center">
        <div className="text-center text-white">
          <p className="text-xl font-semibold text-red-400">{error}</p>
          <button 
            onClick={() => fetchSchedule(currentDate)}
            className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white">
      {/* Header */}
      <header className="bg-black/50 backdrop-blur-md border-b border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl flex items-center justify-center">
                <Tv className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                  TV Schedule
                </h1>
                <p className="text-sm text-gray-400">Premium Channel Guide</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-gray-300">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4" />
                <span>{currentTime.toLocaleTimeString('en-US', { 
                  timeZone: 'America/New_York',
                  hour12: true 
                })}</span>
              </div>
              <div className="text-xs bg-gray-800 px-2 py-1 rounded">ET</div>
            </div>
          </div>
          
          {/* Date Navigation */}
          <div className="mt-4 flex items-center justify-center space-x-6">
            <button 
              onClick={() => changeDate(-1)}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            
            <div className="flex items-center space-x-3 bg-gray-800/50 px-4 py-2 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-400" />
              <span className="font-semibold text-lg">
                {formatDisplayDate(currentDate)}
              </span>
            </div>
            
            <button 
              onClick={() => changeDate(1)}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Schedule Grid */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="relative">
          {/* Time Scale Header */}
          <div className="mb-4 ml-48 relative">
            <div className="flex bg-gray-800/30 rounded-lg p-2">
              {Array.from({ length: 24 }, (_, i) => (
                <div key={i} className="flex-1 text-center text-xs text-gray-400 min-w-[120px]">
                  {i === 0 ? '12 AM' : i < 12 ? `${i} AM` : i === 12 ? '12 PM' : `${i - 12} PM`}
                </div>
              ))}
            </div>
          </div>

          {/* Current Time Indicator Line */}
          <div 
            className="absolute top-16 bottom-0 w-0.5 bg-red-500 z-20 shadow-lg"
            style={{ 
              left: `${192 + getCurrentTimePosition()}px`, // 192px = ml-48
              boxShadow: '0 0 10px rgba(239, 68, 68, 0.5)'
            }}
          >
            <div className="absolute -top-2 -left-2 w-4 h-4 bg-red-500 rounded-full shadow-lg"></div>
          </div>

          {/* Channels and Shows */}
          <div className="space-y-3" ref={scrollContainerRef}>
            {scheduleData?.channels?.map((channel) => (
              <div key={channel.channel_id} className="flex bg-gray-900/50 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors">
                {/* Channel Logo/Name */}
                <div className="w-48 p-4 border-r border-gray-800 flex items-center bg-gray-800/30">
                  <div className="w-12 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded flex items-center justify-center text-xs font-bold mr-3">
                    {channel.channel_name.substring(0, 3).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm">{channel.channel_name}</h3>
                    <p className="text-xs text-gray-400">{channel.shows?.length || 0} programs</p>
                  </div>
                </div>

                {/* Shows Timeline */}
                <div className="flex-1 relative overflow-x-auto">
                  <div className="flex min-w-[2880px]"> {/* 24 hours * 120px */}
                    {channel.shows?.map((show, index) => {
                      const startMinutes = parseTime(show.start_time);
                      const leftPosition = timeToPixels(startMinutes);
                      
                      return (
                        <div
                          key={index}
                          className="absolute h-full cursor-pointer group"
                          style={{ 
                            left: `${leftPosition}px`,
                            width: '200px', // Fixed width for now, could calculate based on duration
                          }}
                          onClick={() => handleShowClick(show)}
                        >
                          <div className="h-full p-2 m-1 bg-gradient-to-r from-gray-700/80 to-gray-600/80 rounded-lg border border-gray-600 hover:border-blue-500 hover:from-gray-600/80 hover:to-gray-500/80 transition-all group-hover:scale-105 group-hover:shadow-lg">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-medium text-blue-300">
                                {show.start_time}
                              </span>
                              <div className="flex items-center space-x-1">
                                {getShowTypeIcon(show.show_type)}
                                <span className="text-xs text-gray-400">
                                  {show.show_type}
                                </span>
                              </div>
                            </div>
                            
                            <h4 className="font-semibold text-sm mb-1 line-clamp-1">
                              {show.title}
                            </h4>
                            
                            {(show.year || show.season) && (
                              <div className="text-xs text-gray-400 mb-1">
                                {show.year && <span>{show.year}</span>}
                                {show.year && show.season && <span> • </span>}
                                {show.season && show.episode && (
                                  <span>{show.season}, {show.episode}</span>
                                )}
                              </div>
                            )}
                            
                            {show.episode_title && (
                              <p className="text-xs text-gray-300 mb-1 line-clamp-1 font-medium">
                                {show.episode_title}
                              </p>
                            )}
                            
                            {show.description && (
                              <p className="text-xs text-gray-400 line-clamp-2">
                                {show.description}
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-black/30 border-t border-gray-800 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-400">
          <p className="text-sm">
            Live TV schedule updated every 15 minutes • Times shown in Eastern Time
          </p>
          <p className="text-xs mt-2">
            Click any program to search on Google • Data sourced from TV Insider
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;