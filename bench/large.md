---
title: Large benchmark fixture
description: A long page with many sections.
---

# Large benchmark fixture

A long document assembled from many small sections, used to measure how render cost scales with page size.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 1 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 1}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 2 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 2}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 3 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 3}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 4 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 4}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 5 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 5}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 6 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 6}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 7 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 7}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 8 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 8}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 9 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 9}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 10 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 10}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 11 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 11}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 12 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 12}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 13 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 13}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 14 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 14}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 15 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 15}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 16 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 16}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 17 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 17}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 18 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 18}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 19 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 19}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 20 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 20}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 21 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 21}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 22 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 22}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 23 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 23}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 24 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 24}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 25 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 25}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 26 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 26}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 27 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 27}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 28 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 28}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 29 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 29}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 30 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 30}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 31 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 31}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 32 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 32}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 33 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 33}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 34 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 34}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 35 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 35}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 36 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 36}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 37 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 37}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 38 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 38}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 39 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 39}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 40 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 40}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 41 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 41}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 42 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 42}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 43 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 43}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 44 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 44}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 45 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 45}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 46 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 46}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 47 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 47}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 48 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 48}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 49 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 49}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 50 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 50}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 51 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 51}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 52 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 52}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 53 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 53}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 54 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 54}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 55 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 55}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 56 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 56}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 57 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 57}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 58 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 58}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 59 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 59}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 60 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 60}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 61 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 61}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 62 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 62}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 63 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 63}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 64 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 64}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 65 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 65}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 66 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 66}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 67 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 67}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 68 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 68}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 69 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 69}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 70 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 70}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 71 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 71}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 72 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 72}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 73 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 73}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 74 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 74}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 75 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 75}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 76 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 76}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 77 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 77}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 78 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 78}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 79 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 79}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 80 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 80}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 81 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 81}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 82 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 82}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 83 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 83}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 84 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 84}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 85 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 85}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 86 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 86}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 87 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 87}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 88 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 88}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 89 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 89}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 90 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 90}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 91 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 91}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 92 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 92}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 93 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 93}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 94 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 94}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 95 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 95}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 96 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 96}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 97 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 97}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 98 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 98}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 99 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 99}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 100 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 100}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 101 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 101}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 102 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 102}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 103 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 103}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 104 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 104}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 105 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 105}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 106 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 106}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 107 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 107}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 108 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 108}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.

## Routing

Routing is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/routes-as-code/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/routes-as-code/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `routes-as-code` | Stable identifier |
| order | 109 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_routes-as-code(options: dict) -> dict:
    """Return the Routing defaults merged with caller options."""
    defaults = {"enabled": True, "order": 109}
    return {**defaults, **options}
```

![Architecture diagram for Routing](./img/routes-as-code.png)

> A note about Routing: keep the configuration next to the code that reads it.

## Content collections

Content collections is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/content-collections/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/content-collections/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `content-collections` | Stable identifier |
| order | 110 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_content-collections(options: dict) -> dict:
    """Return the Content collections defaults merged with caller options."""
    defaults = {"enabled": True, "order": 110}
    return {**defaults, **options}
```

![Architecture diagram for Content collections](./img/content-collections.png)

> A note about Content collections: keep the configuration next to the code that reads it.

## Styling

Styling is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/styling/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/styling/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `styling` | Stable identifier |
| order | 111 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_styling(options: dict) -> dict:
    """Return the Styling defaults merged with caller options."""
    defaults = {"enabled": True, "order": 111}
    return {**defaults, **options}
```

![Architecture diagram for Styling](./img/styling.png)

> A note about Styling: keep the configuration next to the code that reads it.

## Components

Components is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/components/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/components/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `components` | Stable identifier |
| order | 112 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_components(options: dict) -> dict:
    """Return the Components defaults merged with caller options."""
    defaults = {"enabled": True, "order": 112}
    return {**defaults, **options}
```

![Architecture diagram for Components](./img/components.png)

> A note about Components: keep the configuration next to the code that reads it.

## Layouts

Layouts is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layouts/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layouts/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layouts` | Stable identifier |
| order | 113 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layouts(options: dict) -> dict:
    """Return the Layouts defaults merged with caller options."""
    defaults = {"enabled": True, "order": 113}
    return {**defaults, **options}
```

![Architecture diagram for Layouts](./img/layouts.png)

> A note about Layouts: keep the configuration next to the code that reads it.

## Build graph

Build graph is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/build-graph/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/build-graph/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `build-graph` | Stable identifier |
| order | 114 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_build-graph(options: dict) -> dict:
    """Return the Build graph defaults merged with caller options."""
    defaults = {"enabled": True, "order": 114}
    return {**defaults, **options}
```

![Architecture diagram for Build graph](./img/build-graph.png)

> A note about Build graph: keep the configuration next to the code that reads it.

## Incremental builds

Incremental builds is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/incremental-builds/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/incremental-builds/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `incremental-builds` | Stable identifier |
| order | 115 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_incremental-builds(options: dict) -> dict:
    """Return the Incremental builds defaults merged with caller options."""
    defaults = {"enabled": True, "order": 115}
    return {**defaults, **options}
```

![Architecture diagram for Incremental builds](./img/incremental-builds.png)

> A note about Incremental builds: keep the configuration next to the code that reads it.

## Assets

Assets is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/assets/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/assets/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `assets` | Stable identifier |
| order | 116 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_assets(options: dict) -> dict:
    """Return the Assets defaults merged with caller options."""
    defaults = {"enabled": True, "order": 116}
    return {**defaults, **options}
```

![Architecture diagram for Assets](./img/assets.png)

> A note about Assets: keep the configuration next to the code that reads it.

## Images

Images is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/images/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/images/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `images` | Stable identifier |
| order | 117 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_images(options: dict) -> dict:
    """Return the Images defaults merged with caller options."""
    defaults = {"enabled": True, "order": 117}
    return {**defaults, **options}
```

![Architecture diagram for Images](./img/images.png)

> A note about Images: keep the configuration next to the code that reads it.

## Search

Search is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/search/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/search/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `search` | Stable identifier |
| order | 118 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_search(options: dict) -> dict:
    """Return the Search defaults merged with caller options."""
    defaults = {"enabled": True, "order": 118}
    return {**defaults, **options}
```

![Architecture diagram for Search](./img/search.png)

> A note about Search: keep the configuration next to the code that reads it.

## Layers

Layers is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/layers/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/layers/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `layers` | Stable identifier |
| order | 119 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_layers(options: dict) -> dict:
    """Return the Layers defaults merged with caller options."""
    defaults = {"enabled": True, "order": 119}
    return {**defaults, **options}
```

![Architecture diagram for Layers](./img/layers.png)

> A note about Layers: keep the configuration next to the code that reads it.

## Plugins

Plugins is one part of the pipeline. This section is representative prose: a
short paragraph with a [relative link](/guides/plugins/), some `inline code`, and
*emphasis* so the renderer has real inline content to work with rather than a
bare heading.

The section continues with a second paragraph so that hard wrapping, punctuation
and entity handling all appear at least once. Nothing here is unusual; it is the
shape most documentation pages take.

- first item with a [link](/reference/plugins/)
- second item with `code` and *emphasis*
- third item, plain text

| Property | Value | Description |
| --- | --- | --- |
| name | `plugins` | Stable identifier |
| order | 120 | Position in the section order |
| draft | `false` | Hidden in production builds |

```python
def configure_plugins(options: dict) -> dict:
    """Return the Plugins defaults merged with caller options."""
    defaults = {"enabled": True, "order": 120}
    return {**defaults, **options}
```

![Architecture diagram for Plugins](./img/plugins.png)

> A note about Plugins: keep the configuration next to the code that reads it.
