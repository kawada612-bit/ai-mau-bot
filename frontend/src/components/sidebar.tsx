import { motion, AnimatePresence } from 'framer-motion';
import { Plus, MessageSquare, Trash2, X, Menu } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Session } from '@/types/chat';
import { useEffect, useRef } from 'react';

type SidebarProps = {
    sessions: Session[];
    currentSessionId: string | null;
    onSelectSession: (id: string) => void;
    onCreateSession: () => void;
    onDeleteSession: (id: string) => void;
    isOpen: boolean;
    onClose: () => void;
};

export function Sidebar({
    sessions,
    currentSessionId,
    onSelectSession,
    onCreateSession,
    onDeleteSession,
    isOpen,
    onClose,
}: SidebarProps) {
    const sidebarRef = useRef<HTMLDivElement>(null);

    // Close when clicking outside on mobile
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                isOpen &&
                sidebarRef.current &&
                !sidebarRef.current.contains(event.target as Node)
            ) {
                // Only close if screen is narrow (mobile behavior check is usually done via CSS media queries or window width)
                // For simplicity, we assume if isOpen is managed by parent, parent expects it to be modal-like on mobile
                // But here we rely on the parent logic. 
                // Let's implement a simple check: if window width < 768px (md)
                if (window.innerWidth < 768) {
                    onClose();
                }
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen, onClose]);

    return (
        <>
            {/* Mobile Overlay */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="md:hidden fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
                        onClick={onClose}
                    />
                )}
            </AnimatePresence>

            {/* Sidebar Container */}
            <motion.div
                ref={sidebarRef}
                className={cn(
                    "fixed md:static inset-y-0 left-0 z-50 w-72 bg-white/80 backdrop-blur-xl border-r border-white/40 shadow-xl md:shadow-none flex flex-col transition-transform duration-300 ease-in-out",
                    isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
                )}
                initial={false}
            >
                <div className="p-4 flex flex-col h-full">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="font-bold text-slate-700 text-lg flex items-center gap-2">
                            <span className="text-2xl">🗂️</span>
                            履歴
                        </h2>
                        <button
                            onClick={onClose}
                            className="md:hidden p-2 hover:bg-slate-100 rounded-full text-slate-400"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* New Chat Button */}
                    <button
                        onClick={() => {
                            onCreateSession();
                            if (window.innerWidth < 768) onClose();
                        }}
                        className="w-full flex items-center justify-center gap-2 bg-theme-primary text-white py-3 px-4 rounded-xl font-medium shadow-md hover:brightness-110 active:scale-95 transition-all mb-4"
                    >
                        <Plus className="w-5 h-5" />
                        <span>新しいチャット</span>
                    </button>

                    {/* Session List */}
                    <div className="flex-1 overflow-y-auto no-scrollbar space-y-2">
                        {sessions.length === 0 ? (
                            <div className="text-center py-10 text-slate-400 text-sm">
                                まだ会話履歴がありません
                            </div>
                        ) : (
                            sessions.map((session) => (
                                <div
                                    key={session.id}
                                    onClick={() => {
                                        onSelectSession(session.id);
                                        if (window.innerWidth < 768) onClose();
                                    }}
                                    className={cn(
                                        "group relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all",
                                        currentSessionId === session.id
                                            ? "bg-theme-primary/10 text-theme-primary font-medium"
                                            : "hover:bg-slate-50 text-slate-600"
                                    )}
                                >
                                    <MessageSquare className={cn(
                                        "w-5 h-5 flex-shrink-0",
                                        currentSessionId === session.id ? "text-theme-primary" : "text-slate-400"
                                    )} />

                                    <div className="flex-1 min-w-0">
                                        <div className="truncate text-sm">
                                            {session.title || "新しいチャット"}
                                        </div>
                                        <div className="text-[10px] text-slate-400 truncate">
                                            {new Date(session.updatedAt).toLocaleString('ja-JP', {
                                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                            })}
                                        </div>
                                    </div>

                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDeleteSession(session.id);
                                        }}
                                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-50 hover:text-red-500 text-slate-400 rounded-full transition-all"
                                        title="削除"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Footer (Optional) */}
                    <div className="mt-4 pt-4 border-t border-slate-100 text-center text-xs text-slate-400">
                        Powered by Gemini 3 Flash
                    </div>
                </div>
            </motion.div>
        </>
    );
}
