# ATHOS — Design System

**Version** : 1.0 | **Date** : 2026-05-20

---

## 1. Identité visuelle

**Style** : Dark cockpit — opérationnel, dense, premium. Pas de gradients décoratifs. Pas d'animations gadgets. Chaque pixel justifié par une information.

**Inspirations** : Palantir Gotham, Linear, Datadog, Vercel Dashboard, Mission Control NASA.

**Anti-patterns à éviter** :
- Emojis comme icônes (utiliser les caractères Unicode géométriques du NAV)
- Couleurs vives sans information sémantique
- Grands espaces vides non intentionnels
- Ombres portées décoratives

---

## 2. Tokens CSS (`globals.css`)

```css
:root {
  /* Surfaces */
  --bg:         #080808;   /* fond global */
  --surface:    #111114;   /* cartes, panneaux */
  --surface-2:  #1a1a1f;   /* éléments imbriqués, code, badges */

  /* Bordures */
  --border:     #2a2931;   /* lignes, séparateurs, textes désactivés */

  /* Typographie */
  --text:       #f0ede8;   /* texte principal */
  --muted:      #a9a4b2;   /* labels, secondaire */

  /* Accent */
  --accent:     #783cff;   /* claude, action primaire */
  --accent-2:   #aa5aff;   /* athos, variation accent */

  /* Sémantique */
  --green:      #34c759;   /* OK, disponible, succès */
  --red:        #ff453a;   /* erreur, critique, bloqué */
  --blue:       #4a9eff;   /* info, clément, messages */
  --yellow:     #ffd60a;   /* warning, mock, dégradé */

  /* Layout */
  --sidebar-w:  220px;
  --topbar-h:   44px;
}
```

---

## 3. Typographie

**Police** : `-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif`
**Monospace** : Geist Mono (Next.js) pour code, IDs, valeurs techniques

**Échelle** :
| Usage | Taille | Poids | Couleur |
|-------|--------|-------|---------|
| Titre de page | 22px | 600 | --text |
| Titre de section | 11px | 600 | --muted (uppercase, letter-spacing: 1.5) |
| Corps | 13px | 400 | --text |
| Secondaire | 12px | 400 | --muted |
| Métadonnée | 11px | 400 | --muted |
| Micro (badge, tag) | 9–10px | 500–600 | variable |
| Monospace | 11–12px | 400 | --text / --accent |

**Règle** : Ne jamais descendre sous 9px. Le texte monospace sous 11px est réservé aux IDs courts.

---

## 4. Composants partagés (`/components/ui/index.tsx`)

### Card
```tsx
<Card title="Titre optionnel" noPad={false}>
  {children}
</Card>
```
- Background: `--surface`
- Border: `1px solid --border`
- Radius: 8px
- Title: barre supérieure 11px uppercase muted

### StatCard
```tsx
<StatCard label="CA du mois" value="4 800 €" sub="MOCK · mai 2026" color="var(--green)" size="lg" />
```
- Sizes: sm (16px), md (22px), lg (28px)
- Sub-label optionnel en 10px border

### Badge
```tsx
<Badge label="active" variant="green" dot />
```
- Variants: green, red, yellow, blue, accent, muted, border
- Fond: `color-mix(in srgb, {color} 14%, transparent)`
- Border: `color-mix(in srgb, {color} 28%, transparent)`

### EngineBadge
```tsx
<EngineBadge engine="claude_code" />
```
- claude/claude_code → accent
- codex/chatgpt_plus → green
- athos → blue
- ollama → muted

### MockBanner
```tsx
<MockBanner message="Description précise de ce qui est mock." />
```
- Fond jaune translucide, icône ⚠, toujours visible en haut des pages MOCK

### BarChart (CSS)
```tsx
<BarChart data={[{ label: "Jan", value: 1200 }]} height={120} color="var(--accent)" />
```
- Pure CSS, pas de dépendance externe
- Barres proportionnelles à la valeur max

### Gauge
```tsx
<Gauge value={74} max={100} />
```
- Couleur auto selon seuils (80%+ vert, 50%+ jaune, <50% rouge)

### SectionLabel
```tsx
<SectionLabel count={3}>Projets actifs</SectionLabel>
```
- 11px, uppercase, letterSpacing 1.5, --muted

### DataRow
```tsx
<DataRow label="Mode" value="zero_paid_api" mono color="var(--green)" />
```
- Flex, justifyContent: space-between
- Séparé par `1px solid --border`

### PageHeader
```tsx
<PageHeader title="Rapports" subtitle="Daily brief · Récapitulatifs session">
  {/* optional right-side actions */}
</PageHeader>
```
- Titre 22px 600, sous-titre 13px --muted
- Slot `children` aligné à droite (badges, boutons d'action)
- `marginBottom: 24` par convention

### StatusDot
```tsx
<StatusDot ok={true} label="Serveur HUB" />
```
- Dot coloré 7×7, glowing si ok=true
- --green / --red

### RealityBadge
```tsx
<RealityBadge level="RÉEL" />
<RealityBadge level="MOCK" />
<RealityBadge level="MIXTE" />
<RealityBadge level="STATIQUE" />
<RealityBadge level="CODEX" />
```
- Annote la source de données d'une section
- Variants : RÉEL → green · MOCK → yellow · MIXTE → blue · STATIQUE → muted · CODEX → border
- À placer dans les titres de section ou cards pour audit de réalité instantané

### EmptyPanel
```tsx
<EmptyPanel icon="◱" label="Queue vide" detail="Aucune tâche en cours" />
```
- Remplacement standardisé pour tous les états vides
- `icon` optionnel, défaut "◱"
- `label` obligatoire, `detail` optionnel
- Surface + border + radius 8px + padding 32px + centré

### InsetNotice
```tsx
<InsetNotice
  icon="◱"
  text="Endpoint /api/finances non implémenté"
  detail="Interface TypeScript : FinancesSummary dans dashboard/lib/types.ts · Scope Codex P2"
  variant="muted"
/>
```
- Notice intégrée dans le flux de page (pas un banner pleine largeur)
- `variant` : `"muted"` (défaut) | `"yellow"` | `"blue"` | `"green"` | `"red"`
- Couleur du fond et de la bordure dérivée du variant via `color-mix`
- Utiliser systématiquement pour signaler un endpoint backend non encore implémenté
- `detail` optionnel — typiquement l'interface TypeScript + scope Codex

### IntegrationBadge (PCC)
```tsx
<IntegrationBadge tool="Shopify" status="connected" ref="rouge-pivoine.myshopify.com" />
```
- `status` : `"connected"` (vert) | `"configured"` (bleu) | `"error"` (rouge) | `"not_configured"` (gris)
- Affiche : dot de statut · nom de l'outil · référence monospace · label statut
- Utiliser dans les fiches projet pour les intégrations Shopify, GitHub, GSC, Stripe, etc.

### WizardStepHeader (PCC)
```tsx
<WizardStepHeader steps={["Identité", "Présence", "Outils", "Réseaux", "Objectifs", "Agents", "Récap"]} current={2} />
```
- Barre de progression visuelle avec étape active mise en évidence
- Étapes passées en vert, étape active en accent, futures en gris
- Affiche "Étape N sur M" sous la barre

### SocialChannelPill (PCC)
```tsx
<SocialChannelPill platform="instagram" handle="rougepivoine" configured={true} />
```
- Pill avec couleur spécifique par plateforme (instagram:#e1306c, tiktok:#69c9d0, etc.)
- Opacité réduite si `configured={false}`
- Plateformes supportées : instagram, tiktok, linkedin, x, youtube, facebook, pinterest, newsletter

### ProjectSection (PCC)
```tsx
<ProjectSection title="Outils connectés" icon="◱" action={<button>Configurer</button>}>
  {children}
</ProjectSection>
```
- Section wrapper avec titre uppercase + séparateur + slot action optionnel
- Utiliser dans les fiches projet pour chaque groupe d'informations
- `marginBottom: 20` par convention

### ActorStatusPill (Room)
```tsx
<ActorStatusPill actor="claude" label="Claude" color="var(--accent)" lastTs="2026-05-20T18:45:00Z" />
<ActorStatusPill actor="clement" label="Clément" color="var(--blue)" lastTs={undefined} compact />
```
- Pill d'acteur avec dot de statut calculé depuis `lastTs`
- Statuts calculés : `actif` (< 5min, vert) · `récent` (< 1h, jaune) · `silencieux` (> 1h, border) · `absent` (jamais vu, border)
- `compact` supprime le label de statut
- Utiliser dans les panneaux de contexte Room, la sidebar acteurs

### BlockerCallout (Room)
```tsx
<BlockerCallout message="TypeScript error: module not found" actor="claude" ts="2026-05-20T18:30:00Z" />
<BlockerCallout message="Dépendance manquante" compact />
```
- Callout rouge structuré pour les erreurs et blocages
- `compact` pour les listes ou les contextes denses
- Fond rouge translucide + borderLeft 3px rouge
- Utiliser dans la Room pour les messages `type: "error"`, dans les alertes de projet

---

## 5. Layout system

### Classes CSS globales
```css
.ds-root    /* display: flex, column, height: 100vh */
.ds-body    /* display: flex, flex: 1, overflow: hidden */
.ds-sidebar /* width: 220px, fixe, slide mobile */
.ds-main    /* flex: 1, overflow-y: auto, padding: 24px */
```

### Grilles responsives
```css
.grid-auto-2  /* repeat(auto-fit, minmax(260px, 1fr)), gap: 16px */
.grid-auto-3  /* repeat(auto-fit, minmax(200px, 1fr)), gap: 12px */
.grid-auto-4  /* repeat(auto-fit, minmax(140px, 1fr)), gap: 12px */
.grid-nodes   /* repeat(auto-fill, minmax(200px, 1fr)), gap: 8px */
```

### Breakpoints
- `≤ 768px` : sidebar drawer, hamburger affiché, grilles 1 col
- `769–1024px` : sidebar 190px, ajustements grilles
- `> 1024px` : layout full desktop

---

## 6. Icônes

ATHOS utilise les caractères Unicode géométriques comme icônes. Pas d'emoji, pas de SVG externe.

| Caractère | Usage |
|-----------|-------|
| ◈ | Hub / identity |
| ◉ | Room / actif |
| ⬡ | Engine / IA |
| ⟳ | Automation / sync |
| ◫ | Rapport / mémoire |
| ⚠ | Alerte |
| ◱ | Projets / protocol |
| ◲ | SEO / analytics |
| ◳ | Performance / source |
| ◻ | Finances / tool |
| ◼ | Commandes |
| ◾ | CRM |
| ◪ | Roadmap / review |
| ⊙ | Paramètres / guardrail |

---

## 7. Couleurs moteurs

| Moteur | Couleur | CSS var |
|--------|---------|---------|
| Clément | Bleu | --blue |
| Claude / claude_code | Violet | --accent |
| ATHOS | Violet clair | --accent-2 |
| Codex / chatgpt_plus | Vert | --green |
| Erreur | Rouge | --red |
| Heartbeat | Bordure | --border |

---

## 8. États et feedback

| État | Couleur | Pattern |
|------|---------|---------|
| OK / disponible | --green | Dot + badge green |
| Dégradé / warning | --yellow | Dot + badge yellow |
| Erreur / bloqué | --red | Dot + badge red |
| Inactif / SOON | --border | Opacity 0.3-0.5 |
| SSE connecté | --green glowing | box-shadow |
| SSE déconnecté | --red | Pas d'ombre |
| MOCK data | --yellow banner | MockBanner component |

---

## 9. Responsive — règles

- **Tactile minimum** : 44px de hauteur pour toute cible interactive
- **Espacement minimum** : 8px entre cibles adjacentes
- Sidebar mobile : drawer overlay avec backdrop semi-transparent
- Navigation fermée par : tap backdrop, touche Escape, navigation
- `.hide-mobile` masqué sur ≤768px (budget TopBar, etc.)

---

## 10. Dashboard v5 — État produit (2026-05-20)

### Pages et statut source de données

| Page | Route | Données | Composants clés | Notes v5 |
|------|-------|---------|----------------|----------|
| Vue Centrale | /dashboard/hub | MIXTE | ModuleCard, ProductRow, StatCard | PageHeader, module cards mis à jour |
| Room / War Room | /dashboard/room | RÉEL | RoomClient (client), SSE, WarRoomHeader, RoomFilterBar, SessionContextPanel, ActorRosterPanel, ProjectContextCard | v7 — recherche + filtres + sidebar + War Room mode + contexte projet |
| Agents IA | /dashboard/agents | RÉEL | StatCard, EngineBadge, SectionLabel | Refacto complet → composants UI |
| Automations | /dashboard/automations | RÉEL | CodexPendingZone, Card, SectionLabel | Stable |
| Rapports | /dashboard/reports | RÉEL | CodexPendingZone, DataRow | Stable |
| Alertes | /dashboard/alerts | RÉEL | Badge, StatCard, PageHeader | PageHeader ajouté v5 |
| Sites & Projets | /dashboard/projects | RÉEL | StatCard, SectionLabel, PageHeader, EmptyPanel | KPI grid + sections done/blocked v5 |
| SEO Analytics | /dashboard/seo | MOCK | MockBanner, Gauge, PageHeader, InsetNotice | PageHeader + 5 actions IA prioritaires v5 |
| Performance | /dashboard/performance | MIXTE | Gauge, StatusDot, MockBanner | Stable |
| Finances | /dashboard/finances | MIXTE | MockBanner, BarChart, StatCard, PageHeader, InsetNotice | Budget RÉEL + CA MOCK ; restructuré v5 |
| Commandes | /dashboard/commandes | MOCK | MockBanner, PageHeader, InsetNotice | PageHeader + InsetNotice ajoutés v5 |
| CRM / Clients | /dashboard/crm | MOCK | ClientCard | Stable |
| Roadmap | /dashboard/roadmap | STATIQUE | Card, PageHeader | PageHeader ajouté v5 |
| Paramètres | /dashboard/settings | RÉEL | Card, Toggle, PageHeader, Badge | PageHeader RÉEL badge v5 |
| PCC — Nouveau projet | /dashboard/projects/new | PROTOTYPE | WizardStepHeader, IntegrationBadge, SocialChannelPill | Wizard 7 étapes · backend à brancher |
| PCC — Détail projet | /dashboard/projects/[id] | PROTOTYPE | ProjectSection, IntegrationBadge, SocialChannelPill | Fiche Rouge Pivoine + Placerr mockées |

### Convention annotations source

Chaque section ou Card doit être étiquetée par son niveau de réalité.
Utiliser `<RealityBadge level="..." />` dans les titres de section ou en `<SectionLabel>`.
Utiliser `<CodexPendingZone>` pour les fonctionnalités qui attendent une implémentation Codex.
Utiliser `<MockBanner>` en haut de toute page ou section dont les données sont entièrement fictives.
Utiliser `<InsetNotice>` pour signaler un endpoint backend non encore implémenté (Codex scope).

### Pattern Room War Room — v7

La Room utilise un layout en deux colonnes (thread + sidebar collapsible).

**Hiérarchie de la page :**
1. `WarRoomHeader` — SSE status · moteur actif · toggles War Room + sidebar + refresh
2. `RoomFilterBar` — recherche texte · pills acteurs (toggle) · pills types (toggle) · compteur filtré
3. Thread — messages avec rendu spécialisé selon type (checkpoint / error / report / message)
4. Input — zone de saisie avec `placeholder` adapté au mode War Room
5. Sidebar (collapsible, 254px) — `SessionContextPanel` + `ActorRosterPanel` + `ProjectContextCard`

**War Room mode :** toggle visuel activant un glow violet sur le thread (`box-shadow` CSS), un badge `◉ ACTIF`, un `borderBottom` violet sur le header. Pas d'animation lourde — transition 0.3s uniquement.

**Filtres :** 100% frontend sur le thread local. Si total > thread.length → notice jaune de pagination.
