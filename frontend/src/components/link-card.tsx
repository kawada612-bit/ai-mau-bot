'use client';

import { ExternalLink } from 'lucide-react';
import { useState, useEffect } from 'react';

type LinkCardProps = {
    url: string;
};

type OGPData = {
    title: string;
    description: string;
    image: string;
};

export function LinkCard({ url }: LinkCardProps) {
    const [ogpData, setOgpData] = useState<OGPData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    // Extract domain from URL for display
    const getDomain = (url: string) => {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.replace('www.', '');
        } catch {
            return url;
        }
    };

    useEffect(() => {
        const fetchOGP = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ogp`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url }),
                });

                if (!response.ok) throw new Error('OGP fetch failed');

                const data = await response.json();
                setOgpData(data);
            } catch (err) {
                console.error('OGP fetch error:', err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };

        fetchOGP();
    }, [url]);

    // Loading state
    if (loading) {
        return (
            <div className="block mt-3 p-4 rounded-xl bg-gradient-to-br from-cyan-50 to-blue-50 border border-cyan-100 animate-pulse">
                <div className="h-4 bg-cyan-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-cyan-100 rounded w-1/2"></div>
            </div>
        );
    }

    // Error or no OGP data - show simple card
    if (error || !ogpData) {
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

    // Rich OGP card
    return (
        <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="block mt-3 rounded-xl bg-white border border-cyan-100 hover:border-cyan-300 transition-all duration-200 hover:shadow-lg group overflow-hidden"
        >
            {ogpData.image && (
                <div className="w-full h-40 bg-gradient-to-br from-cyan-50 to-blue-50 overflow-hidden">
                    <img
                        src={ogpData.image}
                        alt={ogpData.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                </div>
            )}
            <div className="p-4">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                        <div className="text-xs text-cyan-600 font-medium mb-1">
                            🎫 {getDomain(url)}
                        </div>
                        <h3 className="text-base font-bold text-slate-800 mb-1 line-clamp-2 group-hover:text-cyan-700 transition-colors">
                            {ogpData.title}
                        </h3>
                        {ogpData.description && (
                            <p className="text-sm text-slate-600 line-clamp-2">
                                {ogpData.description}
                            </p>
                        )}
                    </div>
                    <ExternalLink className="w-5 h-5 text-cyan-400 group-hover:text-cyan-600 transition-colors flex-shrink-0" />
                </div>
            </div>
        </a>
    );
}
