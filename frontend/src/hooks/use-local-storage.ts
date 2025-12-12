import { useState, useEffect } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
    // Initialize with function to avoid hydration mismatch
    const [storedValue, setStoredValue] = useState<T>(initialValue);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        try {
            const item = window.localStorage.getItem(key);
            if (item) {
                setStoredValue(JSON.parse(item));
            }
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoaded(true);
        }
    }, [key]);

    const setValue = (value: T | ((val: T) => T)) => {
        try {
            setStoredValue((currentStoredValue) => {
                const valueToStore = value instanceof Function ? value(currentStoredValue) : value;

                if (typeof window !== 'undefined') {
                    window.localStorage.setItem(key, JSON.stringify(valueToStore));
                }

                return valueToStore;
            });
        } catch (error) {
            console.error(error);
        }
    };

    return [storedValue, setValue, isLoaded] as const;
}
