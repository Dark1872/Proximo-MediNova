import { useEffect, useState } from 'react';

const GATEWAY = (import.meta as any).env?.VITE_API_URL || '';
const TOKEN_KEY = 'token';
const USER_KEY = 'user';

/** Token obtenido mediante el login normal. Devuelve null si no hay sesión. */
export function getStoredToken(): string | null {
  const token = localStorage.getItem(TOKEN_KEY);
  return token && token !== 'undefined' && token.trim().length > 10 ? token : null;
}

/**
 * Devuelve el token de la sesión iniciada por el usuario.
 * No existe inicio de sesión automático: si no hay sesión, lanza un error
 * para que la vista pida al usuario iniciar sesión.
 */
export function requireStoredToken(): string {
  const token = getStoredToken();
  if (!token) throw new Error('Sesión no iniciada. Inicia sesión para continuar.');
  return token;
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Rol verificado por el servidor (GET /api/usuarios/me lee el rol de la base de datos).
 * Solo se usa para decidir qué mostrar en la interfaz; la autorización real la aplica siempre el Backend.
 */
export async function fetchVerifiedRole(): Promise<string> {
  const token = getStoredToken();
  if (!token) return '';
  try {
    const res = await fetch(`${GATEWAY}/api/usuarios/me`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) return '';
    const body = await res.json();
    return typeof body?.data?.role === 'string' ? body.data.role : '';
  } catch {
    return '';
  }
}

/** Hook: rol de la sesión verificado por el servidor ('' mientras carga o sin sesión). */
export function useVerifiedRole(): string {
  const [role, setRole] = useState('');
  useEffect(() => {
    let active = true;
    fetchVerifiedRole().then((r) => { if (active) setRole(r); });
    return () => { active = false; };
  }, []);
  return role;
}
