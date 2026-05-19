import { CheckCircle2, CircleAlert, Info, X } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { ToastContext } from "../contexts/ToastContext.js";

const TOAST_TIMEOUT_MS = 4800;

const icons = {
  success: CheckCircle2,
  warning: CircleAlert,
  info: Info
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const notify = useCallback(
    ({ title, message = "", tone = "info" }) => {
      const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      const toast = { id, title, message, tone };
      setToasts((current) => [...current.slice(-3), toast]);
      window.setTimeout(() => dismiss(id), TOAST_TIMEOUT_MS);
      return id;
    },
    [dismiss]
  );

  const value = useMemo(() => ({ notify, dismiss }), [dismiss, notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-region" role="status" aria-live="polite" aria-atomic="false">
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} onDismiss={() => dismiss(toast.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function Toast({ toast, onDismiss }) {
  const Icon = icons[toast.tone] || Info;
  return (
    <section className={`toast ${toast.tone}`}>
      <Icon size={17} aria-hidden="true" />
      <div>
        <strong>{toast.title}</strong>
        {toast.message ? <span>{toast.message}</span> : null}
      </div>
      <button type="button" onClick={onDismiss} aria-label="Dismiss notification">
        <X size={15} aria-hidden="true" />
      </button>
    </section>
  );
}
