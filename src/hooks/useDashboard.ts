import { useState, useEffect, useCallback } from 'react';
import type { DashboardData } from '../types';
import { getStoredToken, requireStoredToken, clearSession } from './useSession';

const GATEWAY = (import.meta as any).env?.VITE_API_URL || '';

/**
 * Token de la sesión iniciada por el usuario mediante el login normal.
 * Ya no existe inicio de sesión automático ni credenciales en el frontend:
 * sin sesión, lanza un error y la vista debe pedir iniciar sesión.
 */
export async function getToken(): Promise<string> {
  return requireStoredToken();
}

async function fetchPublicHome(): Promise<DashboardData> {
  const res = await fetch(`${GATEWAY}/api/home`);
  if (!res.ok) throw new Error('Error fetching data');
  return res.json();
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = getStoredToken();
      if (!token) {
        setData(await fetchPublicHome());
        return;
      }

      const res = await fetch(`${GATEWAY}/api/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.status === 401 || res.status === 403) {
        // Sesión expirada o inválida: se cierra la sesión y se muestran los datos públicos.
        // No se reintenta con ninguna cuenta preconfigurada.
        clearSession();
        setData(await fetchPublicHome());
        return;
      }
      if (!res.ok) throw new Error('Error fetching data');
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Hook para manejar scroll y aplicar clase al header
 * @returns {void}
 */
export function useScrollEffect(): void {
  useEffect(() => {
    const handleScroll = () => {
      const header = document.getElementById('header');
      if (header) {
        header.classList.toggle('scrolled', window.scrollY > 50);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
}
