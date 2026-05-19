import { useContext } from "react";
import { ConsoleAccountContext } from "../contexts/ConsoleAccountContext.js";

export function useConsoleAccount() {
  const value = useContext(ConsoleAccountContext);
  if (!value) {
    throw new Error("useConsoleAccount must be used inside ConsoleAccountProvider");
  }
  return value;
}
