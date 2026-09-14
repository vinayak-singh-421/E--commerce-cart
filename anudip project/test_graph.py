"""
Comprehensive Unit Tests for ProductGraph and Recommendation Engine.
Verifies FR-13 to FR-17 as specified in PRD.md and TECHNICAL.md.
"""
import unittest
from product_graph import ProductGraph, EdgeType, seed_product_graph


class TestProductGraph(unittest.TestCase):

    def setUp(self):
        self.graph = ProductGraph()
        self.sample_catalog = [
            {"id": "p_kb", "name": "Keyboard", "category": "Peripherals", "price": 90.0},
            {"id": "p_mouse", "name": "Mouse", "category": "Peripherals", "price": 50.0},
            {"id": "p_mat", "name": "Desk Mat", "category": "Accessories", "price": 25.0},
            {"id": "p_monitor", "name": "Monitor", "category": "Displays", "price": 300.0},
            {"id": "p_hub", "name": "USB Hub", "category": "Accessories", "price": 60.0}
        ]
        self.catalog_map = {p["id"]: p for p in self.sample_catalog}

    def test_add_edge_bidirectional(self):
        self.graph.add_edge("p_kb", "p_mouse", weight=2.0, edge_type=EdgeType.BOUGHT_TOGETHER)
        self.assertIn("p_kb", self.graph.adjacency)
        self.assertIn("p_mouse", self.graph.adjacency)

        kb_neighbors = self.graph.get_neighbors("p_kb")
        self.assertEqual(len(kb_neighbors), 1)
        self.assertEqual(kb_neighbors[0].to_product_id, "p_mouse")
        self.assertEqual(kb_neighbors[0].weight, 2.0)
        self.assertEqual(kb_neighbors[0].edge_type, EdgeType.BOUGHT_TOGETHER)

        mouse_neighbors = self.graph.get_neighbors("p_mouse")
        self.assertEqual(len(mouse_neighbors), 1)
        self.assertEqual(mouse_neighbors[0].to_product_id, "p_mouse" if False else "p_kb")

    def test_add_existing_edge_increments_weight(self):
        self.graph.add_edge("p_kb", "p_mouse", weight=1.0, edge_type=EdgeType.BOUGHT_TOGETHER)
        self.graph.add_edge("p_kb", "p_mouse", weight=2.5, edge_type=EdgeType.BOUGHT_TOGETHER)

        kb_neighbors = self.graph.get_neighbors("p_kb")
        self.assertEqual(len(kb_neighbors), 1)
        self.assertEqual(kb_neighbors[0].weight, 3.5)

    def test_neighbors_sorted_by_weight_descending(self):
        self.graph.add_edge("p_kb", "p_mouse", weight=1.0, edge_type=EdgeType.SAME_CATEGORY)
        self.graph.add_edge("p_kb", "p_mat", weight=5.0, edge_type=EdgeType.BOUGHT_TOGETHER)
        self.graph.add_edge("p_kb", "p_hub", weight=2.0, edge_type=EdgeType.VIEWED_TOGETHER)

        neighbors = self.graph.get_neighbors("p_kb")
        self.assertEqual(len(neighbors), 3)
        self.assertEqual(neighbors[0].to_product_id, "p_mat")  # weight 5.0
        self.assertEqual(neighbors[1].to_product_id, "p_hub")  # weight 2.0
        self.assertEqual(neighbors[2].to_product_id, "p_mouse")  # weight 1.0

    def test_recommend_excludes_seeds_and_cart_items(self):
        self.graph.add_edge("p_kb", "p_mouse", weight=3.0, edge_type=EdgeType.BOUGHT_TOGETHER)
        self.graph.add_edge("p_kb", "p_mat", weight=2.0, edge_type=EdgeType.VIEWED_TOGETHER)

        # If p_mouse is already in cart, recommendation should only return p_mat
        recs = self.graph.recommend(
            seed_product_ids=["p_kb"],
            exclude_product_ids={"p_mouse"},
            catalog_map=self.catalog_map
        )
        rec_ids = [r["productId"] for r in recs]
        self.assertNotIn("p_kb", rec_ids)
        self.assertNotIn("p_mouse", rec_ids)
        self.assertIn("p_mat", rec_ids)

    def test_multi_seed_score_aggregation(self):
        """
        A candidate connected to MULTIPLE items in cart should receive aggregated score
        and rank higher than a candidate connected to only one.
        """
        # p_mat is connected to BOTH p_kb and p_mouse
        self.graph.add_edge("p_kb", "p_mat", weight=2.0, edge_type=EdgeType.VIEWED_TOGETHER)
        self.graph.add_edge("p_mouse", "p_mat", weight=2.0, edge_type=EdgeType.VIEWED_TOGETHER)

        # p_hub is only connected to p_kb
        self.graph.add_edge("p_kb", "p_hub", weight=2.0, edge_type=EdgeType.VIEWED_TOGETHER)

        recs = self.graph.recommend(
            seed_product_ids=["p_kb", "p_mouse"],
            exclude_product_ids=set(),
            catalog_map=self.catalog_map
        )
        self.assertTrue(len(recs) >= 2)
        # p_mat should rank first because its score is combined from both seeds
        self.assertEqual(recs[0]["productId"], "p_mat")
        self.assertGreater(recs[0]["score"], recs[1]["score"])

    def test_record_co_purchases(self):
        items = [{"productId": "p_kb"}, {"productId": "p_mouse"}, {"productId": "p_mat"}]
        self.graph.record_co_purchases(items, weight_increment=2.0)

        # Pairwise edges should be created
        kb_neighbors = {e.to_product_id: e.weight for e in self.graph.get_neighbors("p_kb")}
        self.assertIn("p_mouse", kb_neighbors)
        self.assertIn("p_mat", kb_neighbors)
        self.assertEqual(kb_neighbors["p_mouse"], 2.0)

    def test_seed_product_graph_builder(self):
        seed_product_graph(self.graph, self.sample_catalog)
        data = self.graph.to_graph_data(self.catalog_map)
        self.assertEqual(data["nodeCount"], 5)
        self.assertGreater(data["edgeCount"], 0)


if __name__ == "__main__":
    unittest.main()
