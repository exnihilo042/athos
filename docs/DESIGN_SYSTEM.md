# ATHOS — Design System

**Version** : 0.6 | **Date** : 2026-05-20

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
