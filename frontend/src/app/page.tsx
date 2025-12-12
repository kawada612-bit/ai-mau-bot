'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Menu, Sparkles, User, Bot, Edit2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLocalStorage } from '@/hooks/use-local-storage';
import { LinkCard } from '@/components/link-card';

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
      text: 'やほす〜！☀️\n今日も会いに来てくれてありがとう！なんかいいことあった？✨',
    },
  ]);
  const [userName, setUserName, isUserLoaded] = useLocalStorage<string>('mau_user_name', 'Guest');
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleRename = () => {
    const newName = prompt("お名前を教えてね！", userName);
    if (newName && newName.trim()) {
      setUserName(newName.trim());
    }
  };

  // Extract URLs from text
  const extractUrls = (text: string): string[] => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.match(urlRegex) || [];
  };

  // Remove URLs from text
  const removeUrls = (text: string): string => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.replace(urlRegex, '').trim();
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userText = inputValue;
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
      // Send last 12 messages for context
      const history = messages.slice(-12).map(m => ({ role: m.role, text: m.text }));

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: userText,
          user_name: userName,
          history: history
        }),
      });

      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      const aiText = data.response; // Get actual text from API

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
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-cyan-300 to-sky-400 p-[2px] shadow-lg shadow-cyan-200">
                <div className="w-full h-full rounded-full bg-white flex items-center justify-center overflow-hidden">
                  <span className="text-xl">🩵</span>
                </div>
              </div>
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-white rounded-full"></span>
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-tight text-slate-700">AIまう</h1>
              <p className="text-xs text-cyan-500 font-medium tracking-wide">Always with you</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRename}
              className="flex items-center space-x-2 hover:bg-black/5 px-3 py-2 rounded-full transition-colors group"
            >
              <span className="text-sm font-medium text-slate-600 group-hover:text-cyan-600 transition-colors">
                {isUserLoaded ? userName : '...'}
              </span>
              <User className="w-4 h-4 text-slate-400 group-hover:text-cyan-500 transition-colors" />
            </button>
            <button className="p-2 rounded-full hover:bg-black/5 transition-colors btn-press">
              <Menu className="w-5 h-5 text-slate-500" />
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
                "flex items-end space-x-2",
                msg.role === 'user' ? "justify-end" : ""
              )}
            >
              {msg.role === 'ai' && (
                <div className="w-8 h-8 rounded-full bg-white flex-shrink-0 flex items-center justify-center text-sm border border-cyan-100 shadow-sm text-cyan-400">
                  🩵
                </div>
              )}

              <div className="max-w-[85%] flex flex-col">
                <div className={cn(
                  "px-4 py-3 shadow-sm whitespace-pre-wrap leading-relaxed text-[15px]",
                  msg.role === 'ai'
                    ? "bg-white/80 border border-white/40 rounded-2xl rounded-bl-none text-slate-700 shadow-sm"
                    : "bg-gradient-to-br from-cyan-400 to-blue-500 text-white rounded-2xl rounded-br-none shadow-lg shadow-cyan-500/20"
                )}>
                  {msg.role === 'ai' ? removeUrls(msg.text) : msg.text}
                  {msg.isStreaming && <span className="inline-block w-1.5 h-4 ml-1 align-middle bg-cyan-300 animate-pulse" />}
                </div>
                {msg.role === 'ai' && extractUrls(msg.text).map((url, idx) => (
                  <LinkCard key={idx} url={url} />
                ))}
              </div>
            </motion.div>
          ))}

          {/* Typing Indicator */}
          <AnimatePresence>
            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex items-end space-x-2"
              >
                <div className="w-8 h-8 rounded-full bg-white flex-shrink-0 flex items-center justify-center text-sm border border-cyan-100 shadow-sm text-cyan-400">
                  🩵
                </div>
                <div className="bg-white/80 border border-white/40 rounded-2xl rounded-bl-none px-4 py-4 shadow-sm flex items-center space-x-1 h-[46px]">
                  <div className="w-2 h-2 bg-cyan-300 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-cyan-300 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-cyan-300 rounded-full animate-bounce"></div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Input Area */}
      <div className="glass absolute bottom-0 w-full p-4 pb-8 z-50">
        <div className="max-w-3xl mx-auto flex items-end space-x-3">
          <button className="p-3 text-slate-400 hover:text-cyan-500 transition-colors btn-press rounded-full hover:bg-cyan-50">
            <Sparkles className="w-6 h-6" />
          </button>

          <div className="flex-1 relative">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              className="glass-input w-full rounded-[20px] px-4 py-3 text-[15px] placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-300/50 text-slate-700 resize-none max-h-32 transition-all no-scrollbar"
              placeholder="まうにメッセージを送る..."
              style={{ minHeight: '48px' }}
            />
          </div>

          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isTyping}
            className="p-3 rounded-full bg-gradient-to-r from-cyan-400 to-sky-500 text-white shadow-lg shadow-cyan-500/20 hover:opacity-90 transition-all btn-press disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5 ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
