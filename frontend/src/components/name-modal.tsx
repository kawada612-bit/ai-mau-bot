'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Sparkles } from 'lucide-react';

interface NameModalProps {
    isOpen: boolean;
    onSave: (name: string) => void;
    currentName: string;
}

export function NameModal({ isOpen, onSave, currentName }: NameModalProps) {
    const [name, setName] = useState(currentName === 'Guest' ? '' : currentName);
    const [error, setError] = useState('');

    useEffect(() => {
        if (isOpen) {
            setName(currentName === 'Guest' ? '' : currentName);
        }
    }, [isOpen, currentName]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const trimmedName = name.trim();
        if (!trimmedName) {
            setError('名前を入力してね！');
            return;
        }
        if (trimmedName.length > 20) {
            setError('20文字以内でお願い！');
            return;
        }
        onSave(trimmedName);
        setError('');
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center px-4">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
                    />

                    {/* Modal Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-sm bg-white/90 backdrop-blur-md border border-white/50 rounded-3xl p-6 shadow-2xl"
                    >
                        <div className="text-center space-y-4">
                            <div className="w-16 h-16 mx-auto bg-gradient-to-tr from-cyan-300 to-sky-400 rounded-full p-[3px] shadow-lg shadow-cyan-200/50">
                                <div className="w-full h-full bg-white rounded-full flex items-center justify-center">
                                    <span className="text-3xl">🩵</span>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <h2 className="text-xl font-bold text-slate-700">はじめまして！</h2>
                                <p className="text-sm text-slate-500">
                                    まうとお話しするために<br />
                                    あなたの名前を教えてください✨
                                </p>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4 pt-2">
                                <div className="relative group">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-cyan-500 transition-colors" />
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={(e) => {
                                            setName(e.target.value);
                                            if (error) setError('');
                                        }}
                                        placeholder="ニックネーム"
                                        className="w-full bg-white border-2 border-slate-100 rounded-xl py-3 pl-10 pr-4 text-slate-700 placeholder:text-slate-300 focus:outline-none focus:border-cyan-300 focus:ring-4 focus:ring-cyan-100 transition-all font-medium"
                                        autoFocus
                                    />
                                </div>
                                {error && (
                                    <p className="text-xs text-red-500 font-bold">{error}</p>
                                )}

                                <button
                                    type="button" // Prevent accidental submit on mobile if user hits enter in some IMEs, though we want enter support. Changed to submit for form handling.
                                    onClick={handleSubmit} // Redundant with form submit but explicit
                                    disabled={!name.trim()}
                                    className="w-full bg-gradient-to-r from-cyan-400 to-sky-500 hover:from-cyan-500 hover:to-sky-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-cyan-500/30 active:scale-95 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Sparkles className="w-5 h-5" />
                                    <span>お話しする</span>
                                </button>
                            </form>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
