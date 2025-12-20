'use client';

import { useState, useRef, useEffect } from 'react';
import { sendGAEvent } from '@next/third-parties/google';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Menu, Sparkles, User, Bot, Edit2, Trash2, Palette, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLocalStorage } from '@/hooks/use-local-storage';
import { LinkCard } from '@/components/link-card';

import { NameModal } from '@/components/name-modal';

type Message = {
  id: string;
  role: 'user' | 'ai';
  text: string;
  isStreaming?: boolean;
};

export default function ChatPage() {
  const [messages, setMessages] = useLocalStorage<Message[]>('mau_chat_history', [
    {
      id: 'welcome',
      role: 'ai',
      text: 'やほす〜！☀️\n今日も会いに来てくれてありがとう！なんかいいことあった？✨\n\n⚠️ お知らせ: チャットは1分間に10通まで送れます。',
    },
  ]);
  const [userName, setUserName, isUserLoaded] = useLocalStorage<string>('mau_user_name', 'Guest');
  const THEMES = ['pink', 'blue', 'mint', 'yellow', 'red', 'white', 'skyblue'] as const;
  const [currentTheme, setCurrentTheme] = useLocalStorage<typeof THEMES[number]>('mau_theme', 'skyblue');

  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isNameModalOpen, setIsNameModalOpen] = useState(false);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [currentMode, setCurrentMode] = useState<string>('MAIN');

  // Suggestions Logic
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

  // Pick suggestions on mount/update
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    // Pick 2 randoms
    const shuffled = [...RANDOM_SUGGESTIONS_POOL].sort(() => 0.5 - Math.random());
    const randoms = shuffled.slice(0, 2);
    setSuggestions([...FIXED_SUGGESTIONS, ...randoms]);
  }, [messages.length]); // Refresh when message count changes (post-send)

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', currentTheme);
  }, [currentTheme]);

  const toggleTheme = () => {
    const currentIndex = THEMES.indexOf(currentTheme as any);
    const nextIndex = (currentIndex + 1) % THEMES.length;
    setCurrentTheme(THEMES[nextIndex]);
  };

  const clearHistory = () => {
    setIsClearModalOpen(true);
  };

  const confirmClearHistory = () => {
    // 1. Set Welcome Message with streaming flag
    const welcomeText = 'やほす〜！☀️\n今日も会いに来てくれてありがとう！なんかいいことあった？✨\n\n⚠️ お知らせ: チャットは1分間に10通まで送れます。';
    const welcomeId = 'welcome-new-' + Date.now();

    setMessages([{
      id: welcomeId,
      role: 'ai',
      text: '',
      isStreaming: true
    }]);
    setIsClearModalOpen(false);

    // 2. Start Typing Effect
    let i = 0;
    const interval = setInterval(() => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === welcomeId ? { ...msg, text: welcomeText.slice(0, i + 1) } : msg
        )
      );
      i++;
      if (i >= welcomeText.length) {
        clearInterval(interval);
        setMessages((prev) =>
          prev.map((msg) => (msg.id === welcomeId ? { ...msg, isStreaming: false } : msg))
        );
      }
    }, 30);
  };

  const deleteMessage = (id: string) => {
    setMessages(prev => prev.filter(m => m.id !== id));
  };



  // Removed static SUGGESTIONS const in favor of state

  const handleSuggestionClick = (text: string) => {
    handleSend(text);
  };

  useEffect(() => {
    if (isUserLoaded && userName === 'Guest') {
      setIsNameModalOpen(true);
    }
  }, [isUserLoaded, userName]);

  const handleRename = () => {
    setIsNameModalOpen(true);
  };

  const handleNameSave = (newName: string) => {
    setUserName(newName);
    setIsNameModalOpen(false);
  };

  // Extract URLs from text
  const extractUrls = (text: string): string[] => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.match(urlRegex) || [];
  };

  // Convert URLs in text to clickable links
  const linkifyText = (text: string) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);

    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-cyan-600 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            {part}
          </a>
        );
      }
      return part;
    });
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async (text?: string) => {
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
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    // 2. Call Backend API
    try {
      // Send GA Event: Message Sent
      sendGAEvent('event', 'chat_message_sent', {
        user_name: userName,
        message_length: userText.length
      });

      // Send last 12 messages for context
      const history = messages.slice(-12).map(m => ({ role: m.role, text: m.text }));

      const startTime = Date.now();
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
      const aiText = data.response; // Get actual text from API
      const aiMode = data.mode;
      if (aiMode) setCurrentMode(aiMode);
      const responseTime = (Date.now() - startTime) / 1000;

      // Send GA Event: Response Received
      sendGAEvent('event', 'ai_response_received', {
        response_length: aiText.length,
        response_time: responseTime
      });

      // --- Start Pseudo-Streaming Logic (Reuse existing structure) ---
      const aiMsgId = (Date.now() + 1).toString();

      setMessages((prev) => [
        ...prev,
        { id: aiMsgId, role: 'ai', text: '', isStreaming: true },
      ]);

      let i = 0;
      const interval = setInterval(() => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMsgId ? { ...msg, text: aiText.slice(0, i + 1) } : msg
          )
        );
        i++;
        if (i >= aiText.length) {
          clearInterval(interval);
          setMessages((prev) =>
            prev.map((msg) => (msg.id === aiMsgId ? { ...msg, isStreaming: false } : msg))
          );
        }
      }, 30);
      // -----------------------------------------------------------

    } catch (error) {
      // Send GA Event: Error
      sendGAEvent('event', 'chat_error', {
        error_message: String(error)
      });
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'ai', text: 'ごめんね、ちょっと調子悪いみたい… (通信エラー) 😵‍💫' }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
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
    <div className="relative h-[100dvh] flex flex-col overflow-hidden text-slate-700 bg-[#F0F9FF] selection:bg-cyan-200/50">
      {/* Background Blobs */}
      <div className="bg-blob" />
      <div className="bg-blob-2" />

      {/* Header */}
      <header className="glass absolute top-0 w-full z-50 transition-all duration-300">
        <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
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
          <div className="flex items-center space-x-1">
            <button
              onClick={clearHistory}
              className="p-2 rounded-full hover:bg-black/5 transition-colors btn-press text-slate-400 hover:text-red-400"
              title="履歴を削除"
            >
              <Trash2 className="w-5 h-5" />
            </button>
            {/* Theme Toggle Hidden as per request (fixed to SkyBlue) */}
            {/* <button
              onClick={toggleTheme}
              className="p-2 rounded-full hover:bg-black/5 transition-colors btn-press text-slate-400 hover:text-theme-primary"
              title="テーマ変更"
            >
              <Palette className="w-5 h-5" />
            </button> */}
            <button
              onClick={handleRename}
              className="flex items-center space-x-2 hover:bg-black/5 px-2 py-2 rounded-full transition-colors group"
            >
              <span className="text-sm font-medium text-slate-600 group-hover:text-theme-primary transition-colors">
                {isUserLoaded ? userName : '...'}
              </span>
              <User className="w-4 h-4 text-slate-400 group-hover:text-theme-primary transition-colors" />
            </button>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <main
        ref={scrollRef}
        className="flex-1 overflow-y-auto pt-24 pb-32 px-4 no-scrollbar scroll-smooth"
      >
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.4, type: "spring" }}
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

          {/* Suggestions */}
          {!isTyping && inputValue === '' && (
            <div className="flex flex-wrap gap-2 justify-end px-4 pb-2">
              {suggestions.map((text) => (
                <button
                  key={text}
                  onClick={() => handleSuggestionClick(text)}
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
      <div className="glass absolute bottom-0 w-full p-4 pb-8 z-50">
        <div className="max-w-3xl mx-auto flex items-end space-x-3">
          <button className="p-3 text-slate-400 hover:text-theme-primary transition-colors btn-press rounded-full hover:bg-black/5">
            <Sparkles className="w-6 h-6" />
          </button>

          <div className="flex-1 relative">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              className="glass-input w-full rounded-[20px] px-4 py-3 text-[15px] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-theme-primary/50 text-slate-700 resize-none max-h-32 transition-all no-scrollbar"
              placeholder="まうにメッセージを送る..."
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
        onSave={handleNameSave}
        currentName={userName}
      />

      {/* Clear History Modal */}
      <AnimatePresence>
        {isClearModalOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/20 backdrop-blur-sm"
              onClick={() => setIsClearModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl relative z-10"
            >
              <h3 className="font-bold text-lg text-slate-700 mb-2">履歴を削除しますか？</h3>
              <p className="text-slate-500 text-sm mb-6">
                これまでの会話がすべて消えてしまいます。<br />
                この操作は元に戻せません。
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={() => setIsClearModalOpen(false)}
                  className="flex-1 py-2.5 rounded-xl bg-slate-100 text-slate-600 font-medium hover:bg-slate-200 transition-colors"
                >
                  キャンセル
                </button>
                <button
                  onClick={confirmClearHistory}
                  className="flex-1 py-2.5 rounded-xl bg-red-400 text-white font-medium hover:bg-red-500 transition-colors shadow-lg shadow-red-200"
                >
                  削除する
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
