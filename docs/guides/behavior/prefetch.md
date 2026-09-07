# Prefetch

epresso is a static, multi-page site — it does not prefetch links by default and
offers no built-in prefetch primitive.

To prefetch, add it yourself in a component `<script>` (e.g. on the layout):

```js
// warm likely destinations on hover / idle
for (const a of document.querySelectorAll('a[data-prefetch]')) {
  a.addEventListener('mouseenter', () => {
    const r = document.createElement('link');
    r.rel = 'prefetch'; r.href = a.href;
    document.head.appendChild(r);
  }, { once: true });
}
```

Every epresso URL is a real static HTML document, so prefetch is just loading that
document's markup ahead of time.
