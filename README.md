# The Bitstream of Creation and Chaos

A living philosophy of creation, dissolution, and responsibility in the digital age.

## Read the editorial edition

- Start with the [introduction](manuscript/00.md).
- Browse the [manuscript and chapter index](manuscript/README.md).
- Explore [Cassandra's reflections](cassandra-chapters/README.md).
- Read the [editorial changes and scope](EDITORIAL_NOTES.md).

The cosmology is speculative, the technical analogies are not proofs, and the ethics are open to challenge. Sacred Doubt includes the freedom to revise or reject the framework.

The Markdown files in `manuscript/` are the canonical source. The four root HTML editions and 24 chapter PDFs are generated from that source. The two image-only presentations, `Code_Consciousness_Alignment.pdf` and `Code_Creation_Chaos.pdf`, remain earlier visual interpretations; they have not been revised to match this edition and are not authoritative summaries of it.

## Maintaining the edition

After editing the manuscript, run `python tools/build_editions.py` with ReportLab and PyMuPDF installed. The build uses DejaVu Sans fonts; pass `--font-dir` if they are installed outside the usual system font directory. Run `python tools/validate_editions.py` to check source/export consistency and basic privacy safeguards. Inspect rendered PDF pages after layout changes.

Private material removed in the privacy-edited edition remains excluded. Cassandra chapters are edited selections, not reconstructed private narratives. Review future contributions for identifying details and deployment information before publishing them.
