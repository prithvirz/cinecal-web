import React, { useState, useEffect } from 'react';
import { Film, Bell, Play, Calendar, Zap, Info, ExternalLink, Star, Clock, TrendingUp, ChevronRight, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const TMDB_API_KEY = 'ab2b22a9681828b737fe97e4825dda36';

const CineCal = () => {
  const [showNotification, setShowNotification] = useState(false);
  const [briefing, setBriefing] = useState({ theatrical: [], streaming: [], loading: true });
  const [currentDate, setCurrentDate] = useState("");
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const fetchTodayContent = async () => {
      const now = new Date();
      const today = now.toISOString().split('T')[0];
      setCurrentDate(today);
      
      try {
        const movieUrl = `https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&region=IN&primary_release_date.gte=${today}&primary_release_date.lte=${today}&with_release_type=3|2`;
        const tvUrl = `https://api.themoviedb.org/3/discover/tv?api_key=${TMDB_API_KEY}&first_air_date.gte=${today}&first_air_date.lte=${today}&with_origin_country=IN`;

        const [movieRes, tvRes] = await Promise.all([fetch(movieUrl), fetch(tvUrl)]);
        const movies = await movieRes.json();
        const tv = await tvRes.json();

        let heroMovies = movies.results;
        if (heroMovies.length === 0) {
          const fallbackRes = await fetch(`https://api.themoviedb.org/3/discover/movie?api_key=${TMDB_API_KEY}&region=IN&sort_by=popularity.desc&primary_release_date.lte=${today}`);
          const fallbackData = await fallbackRes.json();
          heroMovies = fallbackData.results.slice(0, 5);
        }

        setBriefing({
          theatrical: heroMovies,
          streaming: tv.results,
          loading: false
        });
      } catch (error) {
        console.error("Failed to fetch TMDB data", error);
        setBriefing(prev => ({ ...prev, loading: false }));
      }
    };

    fetchTodayContent();
  }, []);

  const triggerTest = () => {
    setShowNotification(true);
    setTimeout(() => setShowNotification(false), 5000);
  };

  const featured = briefing.theatrical[0];

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-cyan-500/30 overflow-x-hidden">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[300px] h-[300px] sm:w-[500px] sm:h-[500px] bg-cyan-600/10 rounded-full blur-[80px] sm:blur-[120px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-[300px] h-[300px] sm:w-[500px] sm:h-[500px] bg-blue-600/10 rounded-full blur-[80px] sm:blur-[120px]" />
      </div>

      {/* Notification Toast */}
      <AnimatePresence>
        {showNotification && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-4 right-4 left-4 sm:left-auto sm:w-auto z-[100] bg-neutral-900/90 backdrop-blur-xl border border-white/10 p-3 sm:p-4 rounded-2xl shadow-2xl flex items-center gap-3"
          >
            <div className="w-9 h-9 sm:w-10 sm:h-10 bg-cyan-500 rounded-full flex items-center justify-center shadow-lg shadow-cyan-500/20 shrink-0">
              <Zap className="w-4 h-4 sm:w-5 sm:h-5 text-black" />
            </div>
            <div className="min-w-0">
              <p className="font-bold text-sm">System Alert</p>
              <p className="text-xs text-neutral-400">YOLO Access: Briefing Protocol Active</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 w-full z-50 px-4 sm:px-6 lg:px-8 py-4 sm:py-6 backdrop-blur-md border-b border-white/5">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-tr from-cyan-600 to-blue-500 rounded-xl flex items-center justify-center rotate-3 shadow-lg">
              <Film className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
            </div>
            <span className="font-black text-lg sm:text-2xl tracking-tighter uppercase italic">CineCal</span>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-6 text-[10px] font-black uppercase tracking-widest text-neutral-400">
            <span className="hover:text-cyan-400 cursor-pointer transition-colors">Intelligence</span>
            <span className="hover:text-cyan-400 cursor-pointer transition-colors">Database</span>
            <div className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-full text-cyan-400 flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-ping" />
              Live Sync
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden w-10 h-10 flex items-center justify-center rounded-xl bg-white/5 border border-white/10"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile Menu Dropdown */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden overflow-hidden"
            >
              <div className="pt-4 pb-2 flex flex-col gap-3">
                <span className="text-sm font-bold uppercase tracking-widest text-neutral-400 hover:text-cyan-400 cursor-pointer transition-colors py-2">Intelligence</span>
                <span className="text-sm font-bold uppercase tracking-widest text-neutral-400 hover:text-cyan-400 cursor-pointer transition-colors py-2">Database</span>
                <div className="px-3 py-2 bg-white/5 border border-white/10 rounded-full text-cyan-400 text-xs font-black uppercase tracking-widest flex items-center gap-2 w-fit">
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-ping" />
                  Live Sync
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-[85vh] sm:h-screen flex items-center pt-20 sm:pt-20">
        <div className="absolute inset-0 z-0">
          <AnimatePresence mode="wait">
            {featured && (
              <motion.div 
                key={featured.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1.5 }}
                className="relative h-full w-full"
              >
                <img 
                  src={`https://image.tmdb.org/t/p/original${featured.backdrop_path}`}
                  className="w-full h-full object-cover grayscale-[0.2] contrast-125"
                  alt="Backdrop"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-[#050505] via-[#050505]/70 to-transparent" />
                <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent to-transparent" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-8 sm:py-0">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="max-w-2xl"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 text-[9px] sm:text-[10px] font-black uppercase tracking-widest mb-4 sm:mb-8">
              <Zap className="w-3 h-3" />
              High Impact Delivery
            </div>
            <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-9xl font-black mb-4 sm:mb-6 tracking-tighter uppercase italic leading-[0.85] sm:leading-[0.8] drop-shadow-2xl break-words">
              {featured?.title || "Loading..."}
            </h1>
            <p className="text-sm sm:text-lg md:text-xl text-neutral-300 mb-6 sm:mb-10 leading-relaxed font-medium max-w-xl line-clamp-3 sm:line-clamp-none">
              {featured?.overview}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
              <button onClick={triggerTest} className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-white text-black font-black uppercase tracking-tighter hover:bg-cyan-400 transition-all flex items-center justify-center gap-3 group text-sm sm:text-base">
                Access Intelligence
                <Play className="w-4 h-4 sm:w-5 sm:h-5 fill-current group-hover:scale-110 transition-transform" />
              </button>
              <button className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-white/5 border border-white/10 backdrop-blur-md font-black uppercase tracking-tighter hover:bg-white/10 transition-all flex items-center justify-center gap-3 text-sm sm:text-base">
                Watch Trailer
                <Info className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Quick Stats Bar */}
      <section className="relative z-10 px-4 sm:px-6 lg:px-8 -mt-8 sm:-mt-12 mb-8 sm:mb-0">
        <div className="max-w-7xl mx-auto">
          <div className="bg-neutral-900/80 backdrop-blur-xl border border-white/5 rounded-2xl sm:rounded-3xl p-4 sm:p-6 grid grid-cols-3 gap-3 sm:gap-6">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 sm:gap-2 mb-1">
                <Film className="w-3 h-3 sm:w-4 sm:h-4 text-cyan-400" />
                <span className="text-lg sm:text-2xl font-black">{briefing.theatrical.length}</span>
              </div>
              <p className="text-[10px] sm:text-xs text-neutral-500 font-bold uppercase tracking-wider">Theatres</p>
            </div>
            <div className="text-center border-x border-white/5">
              <div className="flex items-center justify-center gap-1 sm:gap-2 mb-1">
                <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 text-blue-400" />
                <span className="text-lg sm:text-2xl font-black">{briefing.streaming.length}</span>
              </div>
              <p className="text-[10px] sm:text-xs text-neutral-500 font-bold uppercase tracking-wider">Streaming</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 sm:gap-2 mb-1">
                <Calendar className="w-3 h-3 sm:w-4 sm:h-4 text-emerald-400" />
                <span className="text-lg sm:text-2xl font-black">IN</span>
              </div>
              <p className="text-[10px] sm:text-xs text-neutral-500 font-bold uppercase tracking-wider">Region</p>
            </div>
          </div>
        </div>
      </section>

      {/* Theatrical Releases Section */}
      <section className="relative z-10 py-12 sm:py-20 lg:py-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-2 sm:gap-4 mb-8 sm:mb-12">
          <div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black uppercase italic tracking-tighter mb-1 sm:mb-2">Theatrical Recon</h2>
            <p className="text-neutral-500 font-medium tracking-widest uppercase text-[10px] sm:text-xs">Today's High-Value Targets</p>
          </div>
          <div className="flex items-center gap-2 text-cyan-500 font-mono text-xs">
            <Calendar className="w-3 h-3 sm:w-4 sm:h-4" />
            {currentDate.replace(/-/g, '/')}
          </div>
        </div>

        {/* Mobile: Horizontal Scroll / Desktop: Grid */}
        <div className="flex sm:grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 sm:gap-6 overflow-x-auto sm:overflow-visible pb-4 sm:pb-0 -mx-4 sm:mx-0 px-4 sm:px-0 scrollbar-hide">
          {briefing.theatrical.slice(0, 5).map((item, idx) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              viewport={{ once: true }}
              className="group relative cursor-pointer shrink-0 w-[160px] sm:w-auto"
              onClick={() => setSelectedMedia(item)}
            >
              <div className="aspect-[2/3] overflow-hidden rounded-xl sm:rounded-2xl border border-white/5 bg-neutral-900 shadow-2xl transition-all group-hover:border-cyan-500/50 group-hover:-translate-y-2">
                <img 
                  src={`https://image.tmdb.org/t/p/w500${item.poster_path}`}
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                  alt={item.title}
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60" />
                <div className="absolute bottom-3 left-3 right-3 sm:bottom-4 sm:left-4 sm:right-4">
                  <div className="px-2 py-0.5 bg-cyan-500/20 backdrop-blur-md border border-cyan-500/30 rounded text-[7px] sm:text-[8px] font-black uppercase tracking-widest text-cyan-400 w-fit mb-1.5 sm:mb-2">
                    Verified Release
                  </div>
                  <h3 className="font-bold text-xs sm:text-sm leading-tight uppercase line-clamp-2">{item.title}</h3>
                  {item.vote_average > 0 && (
                    <div className="flex items-center gap-1 mt-1">
                      <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                      <span className="text-[10px] sm:text-xs text-neutral-300 font-bold">{item.vote_average.toFixed(1)}</span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {briefing.theatrical.length === 0 && !briefing.loading && (
          <div className="text-center py-16">
            <Film className="w-12 h-12 text-neutral-700 mx-auto mb-4" />
            <p className="text-neutral-500 font-bold text-sm">No theatrical releases found for today</p>
            <p className="text-neutral-600 text-xs mt-1">Check back tomorrow for new releases</p>
          </div>
        )}

        {briefing.loading && (
          <div className="flex gap-4 overflow-x-auto pb-4 -mx-4 px-4">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="shrink-0 w-[160px] aspect-[2/3] rounded-xl bg-neutral-900 animate-pulse" />
            ))}
          </div>
        )}
      </section>

      {/* Streaming Section */}
      <section className="relative z-10 pb-12 sm:py-20 lg:py-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="mb-8 sm:mb-12">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black uppercase italic tracking-tighter mb-1 sm:mb-2">Streaming Intelligence</h2>
          <p className="text-neutral-500 font-medium tracking-widest uppercase text-[10px] sm:text-xs">Digital Platform Premieres</p>
        </div>

        {/* Mobile: Stacked Cards / Desktop: Side by Side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
          {briefing.streaming.slice(0, 4).map((item, idx) => (
            <motion.div 
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              viewport={{ once: true }}
              className="bg-neutral-900/50 border border-white/5 rounded-2xl sm:rounded-3xl p-4 sm:p-6 lg:p-8 flex gap-4 sm:gap-6 items-center backdrop-blur-md hover:bg-white/5 transition-colors group cursor-pointer"
              onClick={() => setSelectedMedia(item)}
            >
              <img 
                src={`https://image.tmdb.org/t/p/w300${item.poster_path}`}
                className="w-20 h-28 sm:w-28 sm:h-40 lg:w-32 lg:h-48 object-cover rounded-xl sm:rounded-2xl shadow-2xl group-hover:scale-105 transition-transform shrink-0"
                alt={item.name}
                loading="lazy"
              />
              <div className="flex-1 min-w-0">
                <div className="px-2 sm:px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full text-[8px] sm:text-[10px] font-black uppercase tracking-widest text-blue-400 w-fit mb-2 sm:mb-4">
                  TV Premiere
                </div>
                <h3 className="text-base sm:text-xl lg:text-2xl font-black uppercase tracking-tighter mb-2 sm:mb-4 italic leading-none truncate sm:line-clamp-2">{item.name}</h3>
                <p className="text-neutral-400 text-xs sm:text-sm line-clamp-2 sm:line-clamp-3 mb-3 sm:mb-6 hidden sm:block">{item.overview}</p>
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-white group-hover:text-blue-400 transition-colors">
                  Access Specs <ExternalLink className="w-3 h-3" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {briefing.streaming.length === 0 && !briefing.loading && (
          <div className="text-center py-12">
            <Play className="w-10 h-10 text-neutral-700 mx-auto mb-3" />
            <p className="text-neutral-500 font-bold text-sm">No streaming premieres today</p>
          </div>
        )}
      </section>

      {/* Selected Media Modal */}
      <AnimatePresence>
        {selectedMedia && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
            onClick={() => setSelectedMedia(null)}
          >
            <motion.div
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 100, opacity: 0 }}
              className="bg-neutral-900 border border-white/10 rounded-t-3xl sm:rounded-3xl p-6 sm:p-8 w-full sm:max-w-lg max-h-[85vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex gap-4 sm:gap-6">
                <img 
                  src={`https://image.tmdb.org/t/p/w300${selectedMedia.poster_path}`}
                  className="w-24 h-36 sm:w-32 sm:h-48 object-cover rounded-xl shrink-0"
                  alt={selectedMedia.title || selectedMedia.name}
                />
                <div className="flex-1 min-w-0">
                  <h3 className="text-xl sm:text-2xl font-black uppercase tracking-tighter mb-2 italic">{selectedMedia.title || selectedMedia.name}</h3>
                  {selectedMedia.vote_average > 0 && (
                    <div className="flex items-center gap-1 mb-3">
                      <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                      <span className="text-sm font-bold">{selectedMedia.vote_average.toFixed(1)}</span>
                      <span className="text-xs text-neutral-500 ml-1">/ 10</span>
                    </div>
                  )}
                  <p className="text-neutral-400 text-sm line-clamp-4 sm:line-clamp-6">{selectedMedia.overview}</p>
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button className="flex-1 px-4 py-3 bg-cyan-500 text-black font-black uppercase text-sm rounded-xl hover:bg-cyan-400 transition-colors">
                  Get Notified
                </button>
                <button 
                  className="px-4 py-3 bg-white/5 border border-white/10 font-black uppercase text-sm rounded-xl hover:bg-white/10 transition-colors"
                  onClick={() => setSelectedMedia(null)}
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <footer className="relative z-10 py-8 sm:py-12 lg:py-20 border-t border-white/5 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4 sm:gap-8">
          <div className="flex items-center gap-3 opacity-50">
            <Film className="w-4 h-4 sm:w-5 sm:h-5 text-neutral-400" />
            <span className="font-black text-lg sm:text-xl tracking-tighter uppercase italic">CineCal Labs</span>
          </div>
          <p className="text-[9px] sm:text-[10px] text-neutral-600 font-black uppercase tracking-[0.3em] sm:tracking-[0.5em] text-center">
            Autonomous Agent Operations &copy; 2026 HERMES_v2
          </p>
        </div>
      </footer>
    </div>
  );
};

export default CineCal;
