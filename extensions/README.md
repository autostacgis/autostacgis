# STAC schema references

These are pinned, unmodified snapshots for offline validation, not new AutoSTACGIS variants of existing STAC extensions.
[lock.json](lock.json) records versioned URLs, SHA-256 digests, and the separate Data State repository revision.

Use CF for measured quantities, common `unit`/`bands`/`statistics`, Raster for scale/offset, EO for spectral metadata,
Projection for grids, View for angles, Satellite for orbit direction, Grid for tile identity, Product for provider types,
Processing for lineage/levels, and Classification for explicitly known encoded classes.

The new [Data State proposal](https://github.com/autostacgis/stac-data-state) supplies independent processing states
that those extensions do not standardize. Its canonical schema is maintained in that separate repository,
created from the official [STAC extension template](https://github.com/stac-extensions/template).
Its proposed identifier is `https://autostacgis.github.io/stac-data-state/v1.0.0/schema.json`.
Local snapshots work before that URL is published. The proposal is not an endorsed STAC standard.
Standard schema licensing remains with the upstream STAC extension projects (Apache 2.0).
