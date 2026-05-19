import { ExternalLink } from "lucide-react";

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
  return (
    <a className="action-card" href={href}>
      <Icon size={18} aria-hidden="true" />
      <span>
        <strong>{title}</strong>
        <span className="action-body">{body}</span>
      </span>
      <ExternalLink size={15} aria-hidden="true" />
    </a>
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
