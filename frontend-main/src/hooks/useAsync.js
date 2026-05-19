import { useEffect, useState } from "react";

export function useAsync(loader, fallback, deps = []) {
  const [state, setState] = useState({ data: fallback, loading: true, error: null });

  useEffect(() => {
    let active = true;
    setState((current) => ({ ...current, loading: true, error: null }));

    loader()
      .then((data) => {
        if (active) {
          setState({ data, loading: false, error: null });
        }
      })
      .catch((error) => {
        if (active) {
          setState({ data: fallback, loading: false, error });
        }
      });

    return () => {
      active = false;
    };
    // The caller owns refresh cadence through the explicit dependency list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
