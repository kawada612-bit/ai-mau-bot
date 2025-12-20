export type Message = {
    id: string;
    role: 'user' | 'ai';
    text: string;
    isStreaming?: boolean;
};

export type Session = {
    id: string;
    title: string;
    messages: Message[];
    createdAt: number;
    updatedAt: number;
};
