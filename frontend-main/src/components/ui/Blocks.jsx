import { CheckCircle2, CircleAlert } from "lucide-react";

export function CommandBlock({ lines }) {
  return (
    <CodeBlock>
      {lines.map((line) => `$ ${line}`).join("\n")}
    </CodeBlock>
  );
}

export function CodeBlock({ children }) {
  return <pre className="code-block"><code>{children}</code></pre>;
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
