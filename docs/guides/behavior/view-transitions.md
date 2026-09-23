---
order: 352
---

# View Transitions

epresso links perform a normal **full-page navigation** — there is no client-side
router or view-transition system.

To animate between pages you can either:

- rely on CSS entry animations that play on each page load, or
- use the platform's View Transitions API in a component `<script>`:
  `document.startViewTransition(() => location.href = url)` — apply it to your
  internal links so the browser morphs the old view into the new page.

```js
document.addEventListener('click', (e) => {
  const a = e.target.closest('a[data-transition]');
  if (!a) return;
  if (!document.startViewTransition) return;         // fallback: normal nav
  e.preventDefault();
  document.startViewTransition(() => { location.href = a.href; });
});
```
