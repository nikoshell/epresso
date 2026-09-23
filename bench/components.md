---
title: Component page
description: Markdown that routes work through the component pipeline.
---

# Component page

This page mixes prose with allow-listed component tags, so the renderer's
component pass, the placeholder expansion and the Jinja render all run.

<Card title="Getting started">
Follow the [quickstart](/guides/quickstart/) and build your first site.
</Card>

Some prose between components, with a [link](/reference/) and `inline code`.

<Button url="/guides/" variant="primary">Read the guides</Button>

<Button url="/reference/" variant="ghost">Reference</Button>

## Code through a component

A fenced block routed to the code component, so Pygments output is wrapped by a
component rather than emitted as a bare `<pre>`.

```python
def total(values: list[int]) -> int:
    return sum(values)
```

## A second section

More prose so the page is not only components.

> A blockquote with a [link](/about/) inside it.

<Card title="Deployment" variant="compact">
Deploy with `epresso deploy`, or wire it into CI.
</Card>
