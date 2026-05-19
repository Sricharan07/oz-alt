import { ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";

export function Metric({ label, value, icon: Icon, tone = "" }) {
  return (
    <div className={`metric ${tone}`}>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <Icon size={18} aria-hidden="true" />
    </div>
  );
}

export function ActionCard({ title, body, href, icon: Icon }) {
  const external = /^https?:\/\//.test(String(href || ""));
  const Component = external ? "a" : Link;
  const props = external ? { href } : { to: href };
  return (
    <Component className="action-card" {...props}>
      <Icon size={18} aria-hidden="true" />
      <span>
        <strong>{title}</strong>
        <span className="action-body">{body}</span>
      </span>
      <ExternalLink size={15} aria-hidden="true" />
    </Component>
  );
}

export function StatPair({ label, value }) {
  return (
    <div className="stat-pair">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
