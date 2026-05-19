import { CheckCircle2, CircleAlert } from "lucide-react";
import { CopyButton } from "../CopyButton.jsx";

export function CommandBlock({ lines, title = "Terminal" }) {
  const value = lines.map((line) => `$ ${line}`).join("\n");
  return (
    <CodeBlock title={title} copyValue={value}>
      {value}
    </CodeBlock>
  );
}

export function CodeBlock({ children, title = "", copyValue = "" }) {
  return (
    <div className="code-frame">
      {title || copyValue ? (
        <div className="code-toolbar">
          <span>{title}</span>
          {copyValue ? <CopyButton value={copyValue} label="Copy" compact /> : null}
        </div>
      ) : null}
      <pre className="code-block"><code>{children}</code></pre>
    </div>
  );
}

export function Checklist({ items }) {
  return (
    <ul className="checklist">
      {items.map((item) => (
        <li key={item}>
          <CheckCircle2 size={16} aria-hidden="true" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export function StateMessage({ title, body, tone = "" }) {
  return (
    <div className={`state-message ${tone}`}>
      <CircleAlert size={17} aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        {body ? <span>{body}</span> : null}
      </div>
    </div>
  );
}

export function SkeletonRows() {
  return (
    <div className="skeleton-list" aria-label="Loading">
      <span />
      <span />
      <span />
    </div>
  );
}
