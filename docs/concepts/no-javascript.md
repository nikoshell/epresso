# No JavaScript by default

epresso renders **plain HTML**. Nothing ships client JS unless you add it.

Client behavior lives in a `.ep` component's `<script>` block: it is bundled,
deduped, and injected before `</body>` on pages that use the component. There are
no per-element hydration directives — the script runs once on load and enhances
the page. See [Client-side behavior](islands.md.

For interactive islands that need JS only in spots, keep the script small and
scoped, or gate its work on events/observers so the initial page stays static.
