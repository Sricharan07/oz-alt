export function Page({ title, description, actions, children }) {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>{title}</h1>
          {description ? <p>{description}</p> : null}
        </div>
        {actions ? <div className="page-actions">{actions}</div> : null}
      </div>
      {children}
    </div>
  );
}

export function SectionHeader({ title, action }) {
  return (
    <div className="section-header">
      <h2>{title}</h2>
      {action ? <div className="section-action">{action}</div> : null}
    </div>
  );
}

export function Panel({ children, flush = false, className = "" }) {
  return <section className={`panel ${flush ? "flush" : ""} ${className}`.trim()}>{children}</section>;
}
