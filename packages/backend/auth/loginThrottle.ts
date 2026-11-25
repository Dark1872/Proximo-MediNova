/**
 * Limitador de intentos de login (en memoria, por instancia).
 *
 * Tres contadores con ventana deslizante simple (se reinician al vencer la ventana):
 *  - email + IP del cliente : 5 fallos  → bloquea solo a ESE cliente contra esa cuenta.
 *  - IP del cliente         : 20 fallos → frena el "password spraying" desde una IP.
 *  - email (cualquier IP)   : 50 fallos → frena ataques distribuidos contra una cuenta.
 *
 * Un atacante desde una IP ya no bloquea al propietario legítimo (que entra desde otra IP);
 * para bloquear la cuenta globalmente necesitaría ~10 IPs distintas.
 * La IP la determina el Gateway (ver gateway/index.js, cabecera CLIENT_IP_HEADER).
 */

export const CLIENT_IP_HEADER = 'x-farmalink-client-ip';

export interface ThrottleRule {
  name: 'email_ip' | 'ip' | 'email';
  max: number;
}

export const LOGIN_WINDOW_MS = 15 * 60 * 1000;
export const LOGIN_BLOCK_MS = 15 * 60 * 1000;
export const LOGIN_RULES: ThrottleRule[] = [
  { name: 'email_ip', max: 5 },
  { name: 'ip', max: 20 },
  { name: 'email', max: 50 },
];

interface Counter {
  failures: number;
  windowStart: number;
  blockedUntil: number | null;
}

const MAX_TRACKED_KEYS = 50_000;

export class LoginThrottle {
  private counters = new Map<string, Counter>();

  constructor(
    private readonly now: () => number = () => Date.now(),
    private readonly rules: ThrottleRule[] = LOGIN_RULES,
    private readonly windowMs = LOGIN_WINDOW_MS,
    private readonly blockMs = LOGIN_BLOCK_MS,
  ) {}

  private keysFor(email: string, ip: string): Array<[ThrottleRule, string]> {
    const e = email.trim().toLowerCase();
    return this.rules.map((rule) => {
      if (rule.name === 'email_ip') return [rule, `email_ip:${e}|${ip}`];
      if (rule.name === 'ip') return [rule, `ip:${ip}`];
      return [rule, `email:${e}`];
    });
  }

  /** Devuelve el contador vigente (descarta los vencidos). */
  private current(key: string): Counter | undefined {
    const c = this.counters.get(key);
    if (!c) return undefined;
    const t = this.now();
    if (c.blockedUntil !== null && t >= c.blockedUntil) {
      this.counters.delete(key);
      return undefined;
    }
    if (c.blockedUntil === null && t - c.windowStart >= this.windowMs) {
      this.counters.delete(key);
      return undefined;
    }
    return c;
  }

  /** ¿Está bloqueado este intento? Devuelve los segundos restantes del bloqueo más largo. */
  check(email: string, ip: string): { blocked: boolean; remainingSecs: number; rule?: ThrottleRule['name'] } {
    let worst = { blocked: false, remainingSecs: 0 } as { blocked: boolean; remainingSecs: number; rule?: ThrottleRule['name'] };
    for (const [rule, key] of this.keysFor(email, ip)) {
      const c = this.current(key);
      if (c?.blockedUntil) {
        const secs = Math.ceil((c.blockedUntil - this.now()) / 1000);
        if (secs > worst.remainingSecs) worst = { blocked: true, remainingSecs: secs, rule: rule.name };
      }
    }
    return worst;
  }

  recordFailure(email: string, ip: string): void {
    const t = this.now();
    for (const [rule, key] of this.keysFor(email, ip)) {
      const c = this.current(key) ?? { failures: 0, windowStart: t, blockedUntil: null };
      c.failures += 1;
      if (c.failures >= rule.max && c.blockedUntil === null) {
        c.blockedUntil = t + this.blockMs;
        console.warn(`[Auth][Security] Bloqueo de login activado (regla ${rule.name}) hasta ${new Date(c.blockedUntil).toISOString()}`);
      }
      this.counters.set(key, c);
    }
    if (this.counters.size > MAX_TRACKED_KEYS) this.prune();
  }

  /** Login correcto: limpia solo el contador email+IP (los contadores globales siguen frenando ataques). */
  recordSuccess(email: string, ip: string): void {
    for (const [rule, key] of this.keysFor(email, ip)) {
      if (rule.name === 'email_ip') this.counters.delete(key);
    }
  }

  prune(): void {
    for (const key of [...this.counters.keys()]) this.current(key);
  }

  size(): number {
    return this.counters.size;
  }
}

/** IP del cliente tal como la informa el Gateway; si falta o es inválida, la del socket. */
export function resolveClientIp(headerValue: unknown, fallback: string | undefined): string {
  if (typeof headerValue === 'string') {
    const v = headerValue.trim();
    // IPv4 / IPv6 (incl. ::ffff:a.b.c.d); máx. 45 caracteres. Cualquier otra cosa se descarta.
    if (v.length > 0 && v.length <= 45 && /^[0-9a-fA-F:.]+$/.test(v)) return v;
  }
  return fallback || 'unknown';
}
