import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as api from "../api";
import type { AccountUser } from "../types";

type AuthValue = {
  user: AccountUser | null;
  ready: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  register: (payload: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }) => Promise<void>;
  signOut: () => void;
};

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AccountUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // A saved token means the shopper is still signed in after a refresh.
    if (!api.readToken()) {
      setReady(true);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => api.writeToken(null))
      .finally(() => setReady(true));
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await api.login(email, password);
    api.writeToken(result.token);
    setUser(result.user);
  }, []);

  const register = useCallback(
    async (payload: { first_name: string; last_name: string; email: string; password: string }) => {
      const result = await api.signup(payload);
      api.writeToken(result.token);
      setUser(result.user);
    },
    [],
  );

  const signOut = useCallback(() => {
    api.writeToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, ready, signIn, register, signOut }),
    [user, ready, signIn, register, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
