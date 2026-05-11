# ATHOS Engine Contract

## Principe

Athos englobe les moteurs. Un moteur ne possède pas la mémoire, ne décide pas seul des permissions, et ne lance rien en arrière-plan sans journal.

## Ce Que Doit Faire Un Moteur

- S'attacher avec `/api/attach`.
- Utiliser le contexte Athos au lieu de demander à Clément de répéter.
- Reporter via `/api/report`.
- Checkpointer avant/après tâche complexe.
- Respecter `zero_paid_api` si la politique coût le demande.
- Afficher un journal opérationnel: faits, sources, commandes, PID, résultats, blocages.

## Ce Qu'un Moteur Ne Doit Pas Faire

- Répondre comme si Athos n'existait pas.
- Écrire, installer, tuer, pousser, scanner ou contrôler sans validation visible.
- Exposer une chaîne de pensée brute.
- Dépenser via API parce qu'une clé existe.
- Oublier le passage de relais après limite/session.

## Failover

Le failover est réussi seulement si:

- même `context_pack`;
- même objectif;
- même identité Athos;
- même checkpoint;
- report final dans `athos_session_kernel.jsonl`.
