'use client';

import { useState, useRef, useEffect } from 'react';
import { sendGAEvent } from '@next/third-parties/google';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Menu, Sparkles, User, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLocalStorage } from '@/hooks/use-local-storage';
import { LinkCard } from '@/components/link-card';
import { NameModal } from '@/components/name-modal';
import { Sidebar } from '@/components/sidebar';
import { Session, Message } from '@/types/chat';

export default function ChatPage() {
  // --- State: Sessions & User Settings ---
  const [sessions, setSessions, isSessionsLoaded] = useLocalStorage<Session[]>('mau_sessions', []);
  const [currentSessionId, setCurrentSessionId] = useLocalStorage<string | null>('mau_current_session_id', null);

  const [userName, setUserName, isUserLoaded] = useLocalStorage<string>('mau_user_name', 'Guest');
  const [currentTheme, setCurrentTheme] = useLocalStorage<string>('mau_theme', 'skyblue'); // Keeping for compatibility, though fixed to skyblue in UI

  // --- State: UI ---
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false); // Global typing state
  const [isNameModalOpen, setIsNameModalOpen] = useState(false);
  const [currentMode, setCurrentMode] = useState<string>('MAIN');
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);

  // --- Derived State ---
  const currentSession = sessions.find(s => s.id === currentSessionId);
  const messages = currentSession?.messages || [];

  // --- Refs ---
  const scrollRef = useRef<HTMLDivElement>(null);

  // --- Suggestions ---
  const FIXED_SUGGESTIONS = ["次のライブいつ？", "自己紹介して！"];
  const RANDOM_SUGGESTIONS_POOL = [
    "今月のライブ何回？",
    "可愛いって言って！",
    "最近調子どう？",
    "好きな食べ物は？",
    "応援して！",
    "何か面白い話して",
    "おはよう！",
    "おやすみ〜"
  ];
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    const shuffled = [...RANDOM_SUGGESTIONS_POOL].sort(() => 0.5 - Math.random());
    setSuggestions([...FIXED_SUGGESTIONS, ...shuffled.slice(0, 2)]);
  }, [messages.length]);

  // --- Effects ---

  // 1. Theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', currentTheme);
  }, [currentTheme]);

  // 2. Migration Check & Initial Session
  useEffect(() => {
    if (!isSessionsLoaded) return;

    // If no sessions exist, check for old history
    if (sessions.length === 0) {
      const oldHistory = window.localStorage.getItem('mau_chat_history');
      if (oldHistory) {
        try {
          const parsedHistory = JSON.parse(oldHistory);
          const newSession: Session = {
            id: Date.now().toString(),
            title: '以前の会話',
            messages: Array.isArray(parsedHistory) ? parsedHistory : [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          setSessions([newSession]);
          setCurrentSessionId(newSession.id);
        } catch (e) {
          console.error("Migration failed", e);
          createNewSession();
        }
      } else {
        // No old history either => Create fresh session
        createNewSession();
      }
    } else if (!currentSessionId && sessions.length > 0) {
      // If sessions exist but none selected, select the most recent one
      const sorted = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
      setCurrentSessionId(sorted[0].id);
    }
  }, [isSessionsLoaded]);

  // 3. User Name Check
  useEffect(() => {
    if (isUserLoaded && userName === 'Guest') {
      setIsNameModalOpen(true);
    }
  }, [isUserLoaded, userName]);

  // 4. Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping, currentSessionId]);


  // --- Logic: Session Management ---

  const createNewSession = () => {
    const newSession: Session = {
      id: Date.now().toString(),
      title: '新しいチャット',
      messages: [{
        id: 'welcome-' + Date.now(),
        role: 'ai',
        text: 'やほす〜！☀️\n今日も会いに来てくれてありがとう！なんかいいことあった？✨\n\n⚠️ お知らせ: チャットは1分間に10通まで送れます。',
      }],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    setIsSidebarOpen(false); // Close sidebar on mobile
  };

  const updateSessionMessages = (sessionId: string, newMessages: Message[]) => {
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        // Auto-update title if it's the first user message
        let newTitle = s.title;
        if (s.messages.length <= 1 && newMessages.length > 1) {
          const firstUserMsg = newMessages.find(m => m.role === 'user');
          if (firstUserMsg && newTitle === '新しいチャット') {
            newTitle = firstUserMsg.text.slice(0, 20) + (firstUserMsg.text.length > 20 ? '...' : '');
          }
        }

        return {
          ...s,
          messages: newMessages,
          title: newTitle,
          updatedAt: Date.now()
        };
      }
      return s;
    }));
  };

  const deleteSession = (sessionId: string) => {
    const newSessions = sessions.filter(s => s.id !== sessionId);
    setSessions(newSessions);

    if (currentSessionId === sessionId) {
      if (newSessions.length > 0) {
        const sorted = [...newSessions].sort((a, b) => b.updatedAt - a.updatedAt);
        setCurrentSessionId(sorted[0].id);
      } else {
        // Ensure creation happens in next render or force generic update
        // We can just clear current ID and let Effect handle creation, but direct call is safer UI feedback
        // However, standard React practices suggest updating state once.
        // Let's manually trigger a new session creation logic here to be instant
        const newSession: Session = {
          id: Date.now().toString(),
          title: '新しいチャット',
          messages: [{
            id: 'welcome-' + Date.now(),
            role: 'ai',
            text: 'やほす〜！☀️\n今日も会いに来てくれてありがとう！なんかいいことあった？✨\n\n⚠️ お知らせ: チャットは1分間に10通まで送れます。',
          }],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        setSessions([newSession]);
        setCurrentSessionId(newSession.id);
      }
    }
  };


  // --- Logic: Chat ---

  const handleSend = async (text?: string) => {
    if (!currentSessionId || isTyping) return;

    const content = text || inputValue;
    if (!content.trim()) return;

    const userText = content;
    setInputValue('');

    // 1. Add User Message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: userText,
    };

    const updatedMessages = [...messages, userMsg];
    updateSessionMessages(currentSessionId, updatedMessages);
    setIsTyping(true);

    // 2. Call Backend API
    try {
      sendGAEvent('event', 'chat_message_sent', { user_name: userName, message_length: userText.length });

      const history = updatedMessages.slice(-12).map(m => ({ role: m.role, text: m.text }));
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: userText,
          user_name: userName,
          history: history,
          timezone: timezone
        }),
      });

      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      const aiText = data.response;
      if (data.mode) setCurrentMode(data.mode);

      sendGAEvent('event', 'ai_response_received', { response_length: aiText.length });

      // Streaming Effect
      const aiMsgId = (Date.now() + 1).toString();
      const finalMessages = [...updatedMessages, { id: aiMsgId, role: 'ai' as const, text: '', isStreaming: true }];

      updateSessionMessages(currentSessionId, finalMessages);

      let i = 0;
      const interval = setInterval(() => {
        setSessions(currentSessions => currentSessions.map(s => {
          if (s.id === currentSessionId) {
            const newMsgs = s.messages.map(msg =>
              msg.id === aiMsgId ? { ...msg, text: aiText.slice(0, i + 1) } : msg
            );
            if (i >= aiText.length) {
              return { ...s, messages: newMsgs.map(m => m.id === aiMsgId ? { ...m, isStreaming: false } : m), updatedAt: Date.now() };
            }
            return { ...s, messages: newMsgs };
          }
          return s;
        }));

        i++;
        if (i >= aiText.length) {
          clearInterval(interval);
          setIsTyping(false);
        }
      }, 30);

    } catch (error) {
      console.error(error);
      const errorMsg = { id: Date.now().toString(), role: 'ai' as const, text: 'ごめんね、ちょっと調子悪いみたい… (通信エラー) 😵‍💫' };
      updateSessionMessages(currentSessionId, [...updatedMessages, errorMsg]);
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const deleteMessage = (msgId: string) => {
    if (!currentSessionId) return;
    const newMsgs = messages.filter(m => m.id !== msgId);
    updateSessionMessages(currentSessionId, newMsgs);
  };

  // Helpers
  const extractUrls = (text: string): string[] => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.match(urlRegex) || [];
  };

  const linkifyText = (text: string) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);
    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        return (
          <a key={index} href={part} target="_blank" rel="noopener noreferrer" className="underline hover:text-cyan-600 transition-colors" onClick={(e) => e.stopPropagation()}>
            {part}
          </a>
        );
      }
      return part;
    });
  };

  const getModeLabel = (mode: string) => {
    switch (mode) {
      case 'REFLEX': return '⚡ リフレックスモード';
      case 'GENIUS': return '✨ 天才モード';
      case 'SPEED': return '🚀 高速モード';
      case 'MAIN': return '🐎 メインモード';
      case 'PONKOTSU': return '🛡️ ポンコツモード';
      default: return 'Always with you';
    }
  };

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-[#F0F9FF] text-slate-700 font-sans selection:bg-cyan-200/50">

      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onCreateSession={createNewSession}
        onDeleteSession={deleteSession}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full relative w-full transition-all">
        {/* Background Blobs */}
        <div className="bg-blob" />
        <div className="bg-blob-2" />

        {/* Header */}
        <header className="glass absolute top-0 w-full z-10 transition-all duration-300">
          <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="md:hidden p-2 -ml-2 text-slate-400 hover:text-theme-primary transition-colors"
                title="メニューを開く"
              >
                <Menu className="w-6 h-6" />
              </button>

              <div className="relative">
                <div className="w-10 h-10 rounded-full bg-theme-primary p-[2px] shadow-lg shadow-theme-primary/20">
                  <div className="w-full h-full rounded-full bg-white flex items-center justify-center overflow-hidden">
                    <span className="text-xl">🩵</span>
                  </div>
                </div>
                <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-white rounded-full"></span>
              </div>
              <div>
                <h1 className="font-bold text-lg leading-tight tracking-tight text-slate-700">AIまう</h1>
                <p className="text-xs text-theme-primary font-medium tracking-wide">{getModeLabel(currentMode)}</p>
              </div>
            </div>

            <button
              onClick={() => setIsNameModalOpen(true)}
              className="flex items-center space-x-2 hover:bg-black/5 px-2 py-2 rounded-full transition-colors group"
              title="名前を変更"
            >
              <span className="text-sm font-medium text-slate-600 group-hover:text-theme-primary transition-colors">
                {isUserLoaded ? userName : '...'}
              </span>
              <User className="w-4 h-4 text-slate-400 group-hover:text-theme-primary transition-colors" />
            </button>
          </div>
        </header>

        {/* Chat List */}
        <main
          ref={scrollRef}
          className="flex-1 overflow-y-auto pt-24 pb-32 px-4 no-scrollbar scroll-smooth"
        >
          <div className="max-w-3xl mx-auto space-y-6">
            <AnimatePresence mode='popLayout'>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  layout
                  transition={{ duration: 0.3 }}
                  className={cn(
                    "flex items-end space-x-2 group relative",
                    msg.role === 'user' ? "justify-end" : ""
                  )}
                >
                  {msg.role === 'ai' && (
                    <div className="w-8 h-8 rounded-full bg-white flex-shrink-0 flex items-center justify-center text-sm border border-theme-primary/20 shadow-sm text-theme-primary">
                      🩵
                    </div>
                  )}

                  <div className="max-w-[85%] flex flex-col relative">
                    <div
                      onClick={() => msg.role === 'user' && setSelectedMessageId(prev => prev === msg.id ? null : msg.id)}
                      className={cn(
                        "px-4 py-3 shadow-sm whitespace-pre-wrap leading-relaxed text-[15px] cursor-pointer",
                        msg.role === 'ai'
                          ? "bg-white/80 border border-white/40 rounded-2xl rounded-bl-none text-slate-700 shadow-sm"
                          : "bg-theme-bubble-user/10 border border-theme-bubble-user/30 text-slate-700 rounded-2xl rounded-br-none shadow-sm transition-all hover:bg-theme-bubble-user/20"
                      )}>
                      {linkifyText(msg.text)}
                      {msg.isStreaming && <span className="inline-block w-1.5 h-4 ml-1 align-middle bg-theme-primary animate-pulse" />}
                    </div>

                    {msg.role === 'ai' && extractUrls(msg.text).map((url, idx) => (
                      <LinkCard key={idx} url={url} />
                    ))}
                  </div>

                  {msg.role === 'user' && selectedMessageId === msg.id && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteMessage(msg.id);
                      }}
                      className="absolute -left-10 top-1/2 -translate-y-1/2 p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all"
                      title="削除"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Suggestions */}
            {!isTyping && messages.length > 0 && messages[messages.length - 1].role === 'ai' && !messages[messages.length - 1].isStreaming && inputValue === '' && (
              <div className="flex flex-wrap gap-2 justify-end px-4 pb-2">
                {suggestions.map((text) => (
                  <button
                    key={text}
                    onClick={() => handleSend(text)}
                    className="bg-white/60 hover:bg-white border border-theme-primary/20 text-theme-primary text-xs px-3 py-1.5 rounded-full transition-all shadow-sm backdrop-blur-sm select-none"
                  >
                    {text}
                  </button>
                ))}
              </div>
            )}

            {/* Typing Indicator */}
            <AnimatePresence>
              {isTyping && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex items-end space-x-2"
                >
                  <div className="w-8 h-8 rounded-full bg-white flex-shrink-0 flex items-center justify-center text-sm border border-theme-primary/20 shadow-sm text-theme-primary">
                    🩵
                  </div>
                  <div className="bg-white/80 border border-white/40 rounded-2xl rounded-bl-none px-4 py-4 shadow-sm flex items-center space-x-1 h-[46px]">
                    <div className="w-2 h-2 bg-theme-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-theme-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-theme-primary rounded-full animate-bounce"></div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>

        {/* Input Area */}
        <div className="glass absolute bottom-0 w-full p-4 pb-8 z-20">
          <div className="max-w-3xl mx-auto flex items-end space-x-3">
            <button className="p-3 text-slate-400 hover:text-theme-primary transition-colors btn-press rounded-full hover:bg-black/5">
              <Sparkles className="w-6 h-6" />
            </button>

            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isTyping}
                rows={1}
                className="glass-input w-full rounded-[20px] px-4 py-3 text-[15px] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-theme-primary/50 text-slate-700 resize-none max-h-32 transition-all no-scrollbar disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder={isTyping ? "まうが入力中だよ" : "まうにメッセージを送る..."}
                style={{ minHeight: '48px' }}
              />
            </div>

            <button
              onClick={() => handleSend()}
              disabled={!inputValue.trim() || isTyping}
              className="p-3 rounded-full bg-slate-700/90 text-white shadow-lg shadow-slate-500/20 hover:bg-slate-800 transition-all btn-press disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5 ml-0.5" />
            </button>
          </div>
        </div>

        <NameModal
          isOpen={isNameModalOpen}
          onSave={(newName) => {
            setUserName(newName);
            setIsNameModalOpen(false);
          }}
          currentName={userName}
        />
      </div>
    </div>
  );
}
