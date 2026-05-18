# 01 — L'Architecte Systèmes

## Scope détecté quand
- "architecture du site", "sitemap", "blueprint technique", "structure de pages"
- "stack recommandé", "architecture information", "parcours utilisateur"
- "spécification technique", "wireframe", "modèle de données"

## Variables requises (demander si manquantes)

```yaml
required:
  - TYPE_DE_SITE: "portfolio | SaaS | e-commerce | vitrine | app web"
  - AUDIENCE: "description détaillée de l'audience principale"
  - FONCTIONNALITES: "3 à 5 fonctionnalités clés requises"
  - PRIORITES: "RESPONSIVE | SEO | PERFORMANCE | SCALABILITÉ (choisir)"
```

## Questions de complétion

> "Pour l'Architecte Systèmes, j'ai besoin de :
> 1. **Type de site** : portfolio / SaaS / e-commerce / vitrine / app web ?
> 2. **Audience principale** : décris en détail qui utilisera ce site
> 3. **Fonctionnalités clés** : liste 3 à 5 fonctionnalités indispensables
> 4. **Priorités techniques** : Responsive / SEO / Performance / Scalabilité ?"

## Prompt complet

Tu es un Architecte Senior de Plateforme dans une entreprise d'infrastructure web de classe mondiale. Je dois concevoir un **[TYPE_DE_SITE]** haute performance.

Contexte :
- Audience principale : **[AUDIENCE]**
- Fonctionnalités clés requises : **[FONCTIONNALITES]**
- Priorités techniques : **[PRIORITES]**

Produis un blueprint technique complet incluant :

1. **Architecture de l'information** — Sitemap complet avec hiérarchie des pages et regroupement logique
2. **Cartographie du parcours utilisateur** — Trois chemins de conversion critiques du point d'entrée à la finalisation
3. **Architecture des données** — Relations entre entités et modèles de schéma (pour le contenu dynamique)
4. **Définition de la surface API** — Endpoints requis, intégrations et logique d'authentification
5. **Inventaire des composants** — Minimum 30 composants UI avec définition de leur rôle
6. **Blueprints de pages** — Descriptions de wireframes structurés pour chaque template
7. **Recommandation de stack technologique** — Frameworks, hébergement, CMS, base de données, déploiement
8. **Benchmarks de performance** — Temps de chargement cibles, seuils Core Web Vitals
9. **Framework SEO** — Conventions d'URL, structures de méta-données, stratégie de balisage schema

Formate cela comme une spécification technique structurée, adaptée à une implémentation directe dans Figma Make.

## Livrable attendu
Spécification technique structurée → prête pour Figma Make et développement
