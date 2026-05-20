import { athosPost } from "@/lib/athos";
import RoomClient from "@/components/RoomClient";
import type { AthosStatus, RoomEntry } from "@/lib/types";

interface ConversationPayload {
  thread?: RoomEntry[];
  summary?: { total?: number; actors?: Record<string, number> };
}

export default async function RoomPage() {
  const [convResult, statusResult] = await Promise.allSettled([
    athosPost<ConversationPayload>("/api/conversation", { action: "get", limit: 60 }),
    athosPost<AthosStatus>("/api/status"),
  ]);

  const data = convResult.status === "fulfilled" ? convResult.value : {};
  const athosStatus = statusResult.status === "fulfilled" ? statusResult.value : undefined;

  return (
    <div style={{ maxWidth: 1400, height: "calc(100vh - 120px)", display: "flex", flexDirection: "column" }}>
      <RoomClient
        initialThread={data.thread ?? []}
        totalMessages={data.summary?.total ?? 0}
        athosStatus={athosStatus}
      />
    </div>
  );
}
