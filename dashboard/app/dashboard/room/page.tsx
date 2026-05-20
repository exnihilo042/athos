import { athosPost } from "@/lib/athos";
import RoomClient from "@/components/RoomClient";

interface RoomEntry {
  id?: string;
  ts?: string;
  actor?: string;
  type?: string;
  content?: string;
  status?: string;
  task_id?: string;
}

interface ConversationPayload {
  thread?: RoomEntry[];
  summary?: { total?: number; actors?: Record<string, number> };
}

export default async function RoomPage() {
  let data: ConversationPayload = {};

  try {
    data = await athosPost<ConversationPayload>("/api/conversation", { action: "get", limit: 60 });
  } catch {}

  return (
    <div style={{ maxWidth: 900, height: "calc(100vh - 120px)", display: "flex", flexDirection: "column" }}>
      <RoomClient
        initialThread={data.thread ?? []}
        totalMessages={data.summary?.total ?? 0}
      />
    </div>
  );
}
