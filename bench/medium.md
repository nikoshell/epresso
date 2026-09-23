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
