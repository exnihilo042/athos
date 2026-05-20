import { SKILLS, SKILL_STATS, SKILL_WORKFLOWS, ATHO_AGENTS } from "@/lib/skill-registry";
import SkillsClient from "@/components/SkillsClient";
import { PageHeader, Badge } from "@/components/ui";

export default function SkillsPage() {
  return (
    <div style={{ maxWidth: 1300 }}>
      <PageHeader
        title="Skills & Capabilities"
        subtitle="Catalogue opératoire ATHOS — skills Claude disponibles, capacités futures, orchestration à venir"
      >
        <Badge label="LOCAL" variant="green" />
        <Badge label="STATIQUE" variant="muted" />
      </PageHeader>

      <SkillsClient
        skills={SKILLS}
        stats={SKILL_STATS}
        workflows={SKILL_WORKFLOWS}
        agents={ATHO_AGENTS}
      />
    </div>
  );
}
