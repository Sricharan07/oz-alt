import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { useToast } from "../hooks/useToast.js";

export function CopyButton({ value, label = "Copy", compact = false }) {
  const [copied, setCopied] = useState(false);
  const { notify } = useToast();

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      notify({ tone: "success", title: "Copied", message: value.split("\n")[0] });
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      notify({ tone: "warning", title: "Copy failed", message: "Select the command and copy it manually." });
    }
  }

  return (
    <button className={`copy-button ${compact ? "compact" : ""}`} type="button" onClick={copy}>
      {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
      {copied ? "Copied" : label}
    </button>
  );
}
