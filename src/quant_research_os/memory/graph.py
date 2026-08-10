"""Research knowledge-graph helpers over lineage_edges."""

from __future__ import annotations

from typing import Any

from quant_research_os.storage.db import ResearchDB


def research_subgraph(db: ResearchDB, research_id: str) -> dict[str, Any]:
    edges = db.lineage_for(research_id)
    # Also pull experiment edges
    exps = db.list_json("experiments", "research_id=?", (research_id,))
    for e in exps:
        edges.extend(db.lineage_for(e.get("experiment_id", "")))
    # dedupe by id
    seen = set()
    uniq = []
    for edge in edges:
        key = (edge.get("src_id"), edge.get("rel"), edge.get("dst_id"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(
            {
                "src": f"{edge.get('src_type')}:{edge.get('src_id')}",
                "rel": edge.get("rel"),
                "dst": f"{edge.get('dst_type')}:{edge.get('dst_id')}",
            }
        )
    return {"research_id": research_id, "edges": uniq}
