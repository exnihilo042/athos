"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function RefreshButton() {
  const router = useRouter();
  const [spinning, setSpinning] = useState(false);

  function refresh() {
    setSpinning(true);
    router.refresh();
    setTimeout(() => setSpinning(false), 800);
  }

  return (
    <button
      onClick={refresh}
      style={{
        fontSize: 12,
        color: "var(--muted)",
        border: "1px solid var(--border)",
        background: "none",
        padding: "5px 14px",
        borderRadius: 5,
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        gap: 5,
      }}
    >
      <span style={{ display: "inline-block", transform: spinning ? "rotate(180deg)" : "none", transition: "transform 0.4s" }}>
        ↻
      </span>
      Refresh
    </button>
  );
}
