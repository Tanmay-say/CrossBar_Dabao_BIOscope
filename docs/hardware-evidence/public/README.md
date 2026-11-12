# Public Dabao FIFO0 evidence copy

These files are sanitized copies of the local run identified as `d61c047a-8fcc-4b4f-b5f8-f5eb5f2a7a62`. They preserve the observed FIFO0 value and the `HARDWARE_VERIFIED` classification while avoiding publication of unique device and machine identifiers.

Redactions: USB serial, USB topology, persistent by-id path, Linux tty node, prior approval phrase, and the echoed Base64 payload. The public manifest also corrects the zero-filled chunk count based on the pinned Xous implementation; [`amendment.json`](amendment.json) records this correction and hashes the unchanged local source manifest. The original files under the ignored local `artifacts/runs/` directory have not been changed.

Verify all published files with `integrity.json`. Its hashes are over the sanitized copies and are not hashes of the raw local console/manifest files. The original source manifest SHA-256 is recorded in the amendment for provenance.

No dashboard screenshot is included or claimed. This evidence proves a single physical FIFO0 response; it does not prove GPIO pad behavior or an M5Stick protocol session.
