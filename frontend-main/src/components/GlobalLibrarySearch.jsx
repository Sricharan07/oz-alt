import { Search, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { listLibraries } from "../api.js";
import { compactNumber, libraryId, libraryPath } from "../format.js";

export function GlobalLibrarySearch() {
  const location = useLocation();
  const inputRef = useRef(null);
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const [libraries, setLibraries] = useState([]);

  useEffect(() => {
    let active = true;
    listLibraries()
      .then((rows) => {
        if (active) {
          setLibraries(rows);
        }
      })
      .catch(() => {
        if (active) {
          setLibraries([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setFocused(false);
    setQuery("");
  }, [location.pathname]);

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        const tag = document.activeElement?.tagName?.toLowerCase();
        if (tag !== "input" && tag !== "textarea") {
          event.preventDefault();
          inputRef.current?.focus();
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return libraries.slice(0, 6);
    }
    return libraries
      .filter((row) =>
        [row.vendor, row.library, row.version, row.description].some((value) =>
          String(value || "").toLowerCase().includes(needle)
        )
      )
      .slice(0, 7);
  }, [libraries, query]);

  const open = focused && (query || results.length > 0);

  return (
    <div className="global-search" onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) {
        setFocused(false);
      }
    }}>
      <label className="global-search-input">
        <Search size={15} aria-hidden="true" />
        <input
          ref={inputRef}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onFocus={() => setFocused(true)}
          placeholder="Search catalog"
          aria-label="Search catalog"
        />
        {query ? (
          <button type="button" onClick={() => setQuery("")} aria-label="Clear catalog search">
            <X size={14} aria-hidden="true" />
          </button>
        ) : (
          <kbd>/</kbd>
        )}
      </label>
      {open ? (
        <div className="global-search-popover">
          {results.length ? (
            results.map((row) => (
              <Link key={`${row.vendor}/${row.library}/${row.version}`} to={libraryPath(row)} className="global-search-result">
                <strong>{libraryId(row)}</strong>
                <span>{row.version || "latest"} · {compactNumber(row.chunk_count)} chunks</span>
              </Link>
            ))
          ) : (
            <p>No matching libraries.</p>
          )}
        </div>
      ) : null}
    </div>
  );
}
