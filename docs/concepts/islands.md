---
order: 240
---

# Client-side behavior

epresso is **no-JavaScript-by-default**. When you need client-side behavior, put it in a
`.ep` component's **`<script>` block**. There is no separate "islands" directory.

A `<script>` block in a `.ep` file is extracted, bundled with esbuild (falling back to a
raw module when esbuild isn't installed — JS stays optional), and injected before
`</body>` on every page that uses the component. Identical script blocks dedupe to one
file.

```epresso
---
---
<style>.count { color: red; }</style>
<script>
  document.querySelectorAll('.count').forEach((el) => {
    el.addEventListener('click', () => alert('hi'));
  });
</script>
<button class="count">{{ content }}</button>
```

This is **page-level client JS**: it runs once when the page loads and can enhance any
element, including the component's own server-rendered output.

## Relationship to components

- A `.ep` component's `<script>` is plain page-level client JS (bundled, deduped). Good for
  broad behavior — theme toggles, search, analytics, or enhancing all matching elements
  (e.g. code blocks).
- Scoped CSS (`<style>`) scopes the component's styles to its own output.

## What happened to "islands"?

Earlier epresso versions had a separate `islands/<name>.js` mechanism — a `mount(el, props)`
module placed with `{% island %}`. That was **removed**. Client JS now simply lives in `.ep`
component `<script>` blocks that live with the component itself.

## No `client:` directives

epresso has no per-element hydration directives (`client:load`, `client:idle`,
`client:visible`, `client:media`, `client:only`). A component `<script>` runs once
when the page loads and enhances the whole page. For deferred/explicit work, gate
the logic inside the script (e.g. `IntersectionObserver`, user-gesture listeners)
rather than declaring an element-level directive.
