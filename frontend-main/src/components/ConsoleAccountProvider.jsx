import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  changePassword as changePasswordRequest,
  getConsoleAccount,
  logout as logoutRequest,
  revokeCliSession,
  revokeWebSession
} from "../api.js";
import { ConsoleAccountContext } from "../contexts/ConsoleAccountContext.js";

export function ConsoleAccountProvider({ children }) {
  const [state, setState] = useState({
    data: null,
    loading: true,
    error: null,
    authenticated: false
  });

  const refresh = useCallback(async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await getConsoleAccount();
      if (!data?.user) {
        setState({ data: null, loading: false, error: null, authenticated: false });
        return null;
      }
      setState({ data, loading: false, error: null, authenticated: true });
      return data;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setState({ data: null, loading: false, error: null, authenticated: false });
        return null;
      }
      setState({ data: null, loading: false, error, authenticated: false });
      return null;
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const revokeCli = useCallback(
    async (tokenId) => {
      await revokeCliSession(tokenId, state.data?.csrf || "");
      await refresh();
    },
    [refresh, state.data?.csrf]
  );

  const revokeWeb = useCallback(
    async (sessionId) => {
      await revokeWebSession(sessionId, state.data?.csrf || "");
      await refresh();
    },
    [refresh, state.data?.csrf]
  );

  const logout = useCallback(async () => {
    await logoutRequest();
    setState({ data: null, loading: false, error: null, authenticated: false });
  }, []);

  const changePassword = useCallback(
    async ({ currentPassword, newPassword, confirmPassword }) => {
      await changePasswordRequest({
        currentPassword,
        newPassword,
        confirmPassword,
        csrf: state.data?.csrf || ""
      });
      await refresh();
    },
    [refresh, state.data?.csrf]
  );

  const value = useMemo(
    () => ({
      ...state,
      user: state.data?.user || null,
      usage: state.data?.usage || null,
      cliSessions: state.data?.cli_sessions || [],
      webSessions: state.data?.web_sessions || [],
      refresh,
      revokeCli,
      revokeWeb,
      changePassword,
      logout
    }),
    [changePassword, logout, refresh, revokeCli, revokeWeb, state]
  );

  return <ConsoleAccountContext.Provider value={value}>{children}</ConsoleAccountContext.Provider>;
}
