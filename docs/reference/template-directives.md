# Template directives

epresso templates are **Jinja** — there are no HTML-attribute directives such as
`set:text`, `set:html`, `transition:`, or `client:`. The equivalent behavior is
expressed with plain Jinja constructs and template attributes:

| To do this… | use |
|-------------|-----|
| render text (auto-escaped) | `{{ value }}` |
| render raw HTML | `{{ value \| safe }}` or `Markup(value)` |
| run client code | a component `<script>` (see [Client-side behavior](../concepts/islands.md) |
| page transitions | none — static MPA full-page nav (see [View Transitions](../guides/behavior/view-transitions.md) |
| keep a script unbundled / a style global | `is:inline` on `<script>`; `is:global` on `<style>` |

Because output is auto-escaped by default, unescaped HTML is always explicit —
there's no foot-gun.
