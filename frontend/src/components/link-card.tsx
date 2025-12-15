'use client';

import { ExternalLink } from 'lucide-react';

type LinkCardProps = {
    url: string;
};

export function LinkCard({ url }: LinkCardProps) {
    // Extract domain from URL for display
    const getDomain = (url: string) => {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.replace('www.', '');
        } catch {
            return url;
        }
    };

    // Simple link card without OGP fetching
    return (
        <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="block mt-3 p-4 rounded-xl bg-gradient-to-br from-cyan-50 to-blue-50 border border-cyan-100 hover:border-cyan-300 transition-all duration-200 hover:shadow-md group"
        >
            <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                    <div className="text-xs text-cyan-600 font-medium mb-1">
                        🎫 チケット情報
                    </div>
                    <div className="text-sm text-slate-700 font-medium truncate group-hover:text-cyan-700 transition-colors">
                        {getDomain(url)}
                    </div>
                </div>
                <ExternalLink className="w-5 h-5 text-cyan-400 group-hover:text-cyan-600 transition-colors flex-shrink-0 ml-2" />
            </div>
        </a>
    );
}
