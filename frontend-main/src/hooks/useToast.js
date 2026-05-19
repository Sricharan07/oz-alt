import { useContext } from "react";
import { ToastContext } from "../contexts/ToastContext.js";

export function useToast() {
  const value = useContext(ToastContext);
  if (!value) {
    throw new Error("useToast must be used inside ToastProvider");
  }
  return value;
}
