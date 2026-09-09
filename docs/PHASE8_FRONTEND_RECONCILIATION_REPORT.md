# Phase 8 — SvelteKit Frontend Reconciliation

## Delivered

- `frontend/` remains the only active frontend source.
- Svelte type-check configuration now uses a real `tsconfig.json`; the missing
  `jsconfig.json` reference was removed.
- Vite proxies `/api` to the centralized backend with the required prefix
  rewrite and proxies `/ws` with WebSocket upgrade support.
- The production Docker image copies SvelteKit's `build/` output, not the
  incompatible `dist/` directory.
- The monitoring page now loads existing sessions, creates/stops real backend
  sessions, and displays only values received from the stream. Missing values
  remain `--`; no fallback physiological values are generated.
- Generic service pages now call only verified current backend endpoints and
  no longer display fabricated signal quality, confidence, privacy, or model
  metrics.
- Federated-learning navigation is explicitly marked `DEFERRED`, and its
  overview explains the centralized-only release scope.
- The frontend displays `AUTH / DISABLED BY SCOPE`; no login or token flow is
  required by the active application.

## Verification

From `frontend/`:

```text
npm run check   # svelte-check found 0 errors (119 non-blocking warnings)
npm run build   # passed; SvelteKit wrote the site to build/
```

The remaining Svelte warnings are pre-existing unused CSS/deprecation warnings
in migrated visual pages; they do not prevent type-checking or production
build. Research and hardware/federated pages that are not backed by current
centralized APIs remain marked or treated as unavailable rather than evidence.
