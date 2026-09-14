"""
Product Recommendation Engine using an In-Memory Adjacency List Graph.
Follows requirements in PRD.md (FR-13 to FR-17) and TECHNICAL.md (Section 3.3).
"""
from typing import Dict, List, Set, Optional, Any


class EdgeType:
    BOUGHT_TOGETHER = "BOUGHT_TOGETHER"
    SAME_CATEGORY = "SAME_CATEGORY"
    VIEWED_TOGETHER = "VIEWED_TOGETHER"

    WEIGHT_MULTIPLIERS = {
        BOUGHT_TOGETHER: 2.5,   # Highest confidence signal
        SAME_CATEGORY: 1.0,     # Moderate category affinity
        VIEWED_TOGETHER: 1.5    # Complementary peripheral affinity
    }


class ProductEdge:
    """
    Weighted edge in the product relationship graph.
    """
    def __init__(self, to_product_id: str, weight: float, edge_type: str):
        self.to_product_id: str = to_product_id
        self.weight: float = float(weight)
        self.edge_type: str = edge_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "to": self.to_product_id,
            "weight": round(self.weight, 2),
            "type": self.edge_type
        }


class ProductGraph:
    """
    Adjacency list representation of product-to-product relationships.
    O(1) edge insertion, O(k log k) neighbor ranking.
    """
    def __init__(self):
        # Map<productId, List<ProductEdge>>
        self.adjacency: Dict[str, List[ProductEdge]] = {}

    def add_node(self, product_id: str) -> None:
        if product_id not in self.adjacency:
            self.adjacency[product_id] = []

    def add_edge(
        self,
        product_a: str,
        product_b: str,
        weight: float = 1.0,
        edge_type: str = EdgeType.SAME_CATEGORY,
        bidirectional: bool = True
    ) -> None:
        """
        O(1) operation:
        Adds or increments an edge between product_a and product_b.
        """
        if product_a == product_b:
            return

        self.add_node(product_a)
        self.add_node(product_b)

        self._upsert_directed_edge(product_a, product_b, weight, edge_type)
        if bidirectional:
            self._upsert_directed_edge(product_b, product_a, weight, edge_type)

    def _upsert_directed_edge(self, from_id: str, to_id: str, weight: float, edge_type: str) -> None:
        for edge in self.adjacency[from_id]:
            if edge.to_product_id == to_id and edge.edge_type == edge_type:
                edge.weight += weight
                return
        self.adjacency[from_id].append(ProductEdge(to_id, weight, edge_type))

    def get_neighbors(self, product_id: str, limit: Optional[int] = None) -> List[ProductEdge]:
        """
        O(k log k) neighbor lookup sorted by weight descending.
        """
        if product_id not in self.adjacency:
            return []

        neighbors = sorted(self.adjacency[product_id], key=lambda e: e.weight, reverse=True)
        if limit is not None:
            return neighbors[:limit]
        return neighbors

    def record_co_purchases(self, items: List[Any], weight_increment: float = 1.0) -> None:
        """
        Batch/Real-time graph update:
        Every pair of items co-purchased in the same order receives a BOUGHT_TOGETHER edge.
        """
        product_ids = list(set([getattr(it, "product_id", None) or it.get("productId") for it in items]))
        for i in range(len(product_ids)):
            for j in range(i + 1, len(product_ids)):
                p_a = product_ids[i]
                p_b = product_ids[j]
                self.add_edge(p_a, p_b, weight=weight_increment, edge_type=EdgeType.BOUGHT_TOGETHER, bidirectional=True)

    def recommend(
        self,
        seed_product_ids: List[str],
        exclude_product_ids: Optional[Set[str]] = None,
        catalog_map: Optional[Dict[str, Dict[str, Any]]] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        FR-13 & FR-14 Recommendation Heuristic:
        1. Traverse neighbors from each seed product.
        2. Aggregate and sum weighted scores across multiple seeds.
        3. Filter out items in exclude_product_ids (e.g. items already in cart).
        4. Sort by aggregate score descending and return top-N.
        """
        if not seed_product_ids:
            return []

        # Sanitize seeds
        valid_seeds = [s for s in seed_product_ids if s and s in self.adjacency]
        if not valid_seeds:
            return []

        exclude = set(exclude_product_ids or [])
        exclude.update(valid_seeds)

        candidate_scores: Dict[str, float] = {}
        candidate_reasons: Dict[str, List[str]] = {}

        for seed_id in valid_seeds:
            neighbors = self.get_neighbors(seed_id)
            seed_name = catalog_map.get(seed_id, {}).get("name", seed_id) if catalog_map else seed_id

            for edge in neighbors:
                target_id = edge.to_product_id
                if target_id in exclude:
                    continue

                multiplier = EdgeType.WEIGHT_MULTIPLIERS.get(edge.edge_type, 1.0)
                score_contribution = edge.weight * multiplier

                candidate_scores[target_id] = candidate_scores.get(target_id, 0.0) + score_contribution

                if target_id not in candidate_reasons:
                    candidate_reasons[target_id] = []

                if edge.edge_type == EdgeType.BOUGHT_TOGETHER:
                    reason = f"Frequently bought with {seed_name}"
                elif edge.edge_type == EdgeType.VIEWED_TOGETHER:
                    reason = f"Often viewed together with {seed_name}"
                else:
                    reason = f"Related category to {seed_name}"

                if reason not in candidate_reasons[target_id]:
                    candidate_reasons[target_id].append(reason)

        # Sort candidates by aggregate score descending
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for prod_id, score in sorted_candidates[:limit]:
            prod_info = catalog_map.get(prod_id, {}) if catalog_map else {}
            results.append({
                "productId": prod_id,
                "name": prod_info.get("name", prod_id),
                "category": prod_info.get("category", "General"),
                "price": prod_info.get("price", 0.0),
                "image": prod_info.get("image", "📦"),
                "score": round(score, 2),
                "reasons": candidate_reasons.get(prod_id, ["Recommended based on your activity"]),
                "primaryReason": candidate_reasons.get(prod_id, ["Recommended item"])[0]
            })

        return results

    def to_graph_data(self, catalog_map: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Serializes graph to { nodes: [...], edges: [...] } for interactive visualization.
        """
        nodes = []
        for pid in self.adjacency.keys():
            info = catalog_map.get(pid, {}) if catalog_map else {}
            nodes.append({
                "id": pid,
                "label": info.get("name", pid),
                "category": info.get("category", "General"),
                "image": info.get("image", "📦"),
                "degree": len(self.adjacency[pid])
            })

        edges = []
        seen_pairs = set()
        for from_id, edge_list in self.adjacency.items():
            for edge in edge_list:
                pair_key = tuple(sorted([from_id, edge.to_product_id])) + (edge.edge_type,)
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    edges.append({
                        "source": from_id,
                        "target": edge.to_product_id,
                        "weight": round(edge.weight, 2),
                        "type": edge.edge_type
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "nodeCount": len(nodes),
            "edgeCount": len(edges)
        }


def seed_product_graph(graph: ProductGraph, catalog: List[Dict[str, Any]], orders: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Batch Graph Builder:
    Seeds base catalog category edges, complementary associations, and co-purchase history.
    """
    # 1. Register all products as nodes
    for prod in catalog:
        graph.add_node(prod["id"])

    # 2. SAME_CATEGORY edges
    for i in range(len(catalog)):
        for j in range(i + 1, len(catalog)):
            if catalog[i]["category"] == catalog[j]["category"]:
                graph.add_edge(
                    catalog[i]["id"],
                    catalog[j]["id"],
                    weight=1.0,
                    edge_type=EdgeType.SAME_CATEGORY
                )

    catalog_ids = {p["id"] for p in catalog}
    complementary_pairs = [
        ("prod_kb", "prod_mat", 2.0),       # Keyboard + Desk Mat
        ("prod_mouse", "prod_mat", 2.0),    # Mouse + Desk Mat
        ("prod_kb", "prod_mouse", 2.5),     # Keyboard + Mouse
        ("prod_monitor", "prod_hub", 3.0),  # Monitor + USB-C Dock
        ("prod_headphones", "prod_kb", 1.5) # Headphones + Keyboard
    ]
    for p_a, p_b, weight in complementary_pairs:
        if p_a in catalog_ids and p_b in catalog_ids:
            graph.add_edge(p_a, p_b, weight=weight, edge_type=EdgeType.VIEWED_TOGETHER)

    # 4. Ingest co-purchase edges from historical orders if any
    if orders:
        for order in orders:
            items = order.get("items", [])
            if len(items) > 1:
                graph.record_co_purchases(items, weight_increment=1.5)
