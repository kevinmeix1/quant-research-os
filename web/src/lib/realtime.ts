"use client";

import { useEffect, useRef } from "react";
import { mutate } from "swr";

const DEFAULT_BASE =
  process.env.NEXT_PUBLIC_QROS_API_URL ?? "http://127.0.0.1:8002";

/** Subscribe to SSE research events and invalidate SWR caches. */
export function useResearchEvents(enabled = true) {
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    const key =
      process.env.NEXT_PUBLIC_QROS_API_KEY ||
      window.localStorage.getItem("qros_api_key");
    // EventSource cannot set headers; when API key required, fall back to polling via SWR.
    if (key) return;

    let es: EventSource;
    try {
      es = new EventSource(`${DEFAULT_BASE}/events/stream`);
    } catch {
      return;
    }
    esRef.current = es;

    const refresh = () => {
      void mutate((k) => typeof k === "string" && k.includes("research"), undefined, {
        revalidate: true,
      });
      void mutate("overview-research");
      void mutate("research-list");
    };

    es.addEventListener("research.updated", refresh);
    es.onerror = () => {
      // Browser will retry; keep silent for workstation density.
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [enabled]);
}
