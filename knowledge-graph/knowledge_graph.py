from weaviate_client import WeaviateGraph
from code_executor import execute_snippet
from openai_client import ask_for_code, generate_node_summary

from weaviate.classes.query import Filter, MetadataQuery

import pandas as pd
from typing import Any, Dict, List
import json

class KnowledgeGraph:
	def __init__(self, user_data):
		self.graph = WeaviateGraph()
		self.data = user_data


	def query(self, question: str) -> Any:
		"""Use the available knowledge base to answer the question.
		Execute solution and create a new node with the answer.
		Connect the new node to relevant nodes in the knowledge base."""

		# Find existing context nodes that are relevant
		relevant_nodes = self.find_relevant_nodes(question)	
		known_results = self._gather_known_results(relevant_nodes)

		# Generate and execute algorithm to answer the question
		code = self.generate_algorithm(question, known_results)
		result_buffer = self.execute_algorithm(code, known_results)
  
		# Insert new node into the knowledge graph
		self.graph.insert_node(
			user_query=question,
			algorithm=code,
			buffer=str(result_buffer),
			summary=generate_node_summary(code + "\n" + question),
			parent_ids=relevant_nodes
		)

		return result_buffer


	def find_relevant_nodes(self, question: str):
		"""Search knowledge base.
		Find the childest node containing relevant information to the question
		(i.e. no descendants contain relevant information)."""
		
		if (self.graph.has_nodes() is False):
			return []

		nodes = self.graph.nodes

		# Vector search to get top-K relevant nodes
		top_k = 8
		hits = nodes.query.near_text(
			query=question,
			limit=top_k,
			return_metadata=MetadataQuery(distance=True),
		)

		# Filter to get youngest nodes (no descendants in hits)
		relevant_leaf_ids: list[str] = []
		for obj in hits.objects:
			candidate_id = str(obj.uuid)
			child_hits = nodes.query.near_text(
				query=question,
				limit=1,
				filters=Filter.by_ref(link_on="parents").by_id().equal(candidate_id),
			)
			# keep only those that have NO relevant children
			if not child_hits.objects:
				relevant_leaf_ids.append(candidate_id)

		return relevant_leaf_ids

  
	def _gather_known_results(self, node_ids: list[str]) -> Dict[str, Any]:
		"""From a list of node IDs, gather their buffers as known results,
  		ready variables that the AI can reference to avoid recomputation."""
  
		known: Dict[str, Any] = {}

		for nid in node_ids:
			try:
				# Reuse the helper that maps summary -> buffer (string)
				var_map = self.graph.get_variable(nid)  # {summary: buffer_str}
				for summary, buf in var_map.items():
					# Try to JSON-decode the buffer so downstream code can use native types
					try:
						known[summary] = json.loads(buf)
					except Exception:
						# Fall back to the raw string if it isn't JSON
						known[summary] = buf
			except Exception:
				# If a node is missing or unreadable, just skip it
				continue

		return known


	def generate_algorithm(self, question: str, known_results: Dict[str, Any]) -> str:
		"""Generate an algorithm to answer the question based on relevant nodes and user data."""

		# We let the AI know that these known results are available
		known_results_preview = json.dumps(
			{
				k: (v if isinstance(v, (int, float, bool, dict, list)) 
				    else (str(v)[:240] + ("..." if len(str(v)) > 240 else "")))
				for k, v in known_results.items()
			},
			ensure_ascii=False,
			default=str,
			indent=2,
		)

		# Prompt to generate code
		system_instructions = """
			TASK
			- Write Python code that computes an answer to the user's question based on a pandas DataFrame.
			- The DataFrame is provided in a variable named `user_data` and contains all the data you need.

			CONTRACT
			- Define a function with EXACT signature:

			def answer(user_data: pd.DataFrame) -> Any:

			- The function MUST:
				- Use `user_data` directly (do not read files or make network calls).
				- Be deterministic and side-effect free.
				- Treat `known_results` as read-only "constants" you may reference to avoid recomputing.
				- Use `known_results` where possible to improve efficiency.
				- You MAY define helper functions inside the module, but the entry point is `answer`.
				- Prefer vectorized pandas operations; avoid O(n^2) Python loops on rows.
				- Validate assumptions (e.g., column names) and raise a clear `ValueError` if missing.

			OUTPUT
			- Output ONLY valid Python code for a module that defines `answer(user_data)`.
			- No Markdown, no comments outside code blocks.

			PANDAS
			Specification for the `user_data` DataFrame:
			- It contains the following columns: 'purchase' (str), 'price' (float), 'category' (str), 'timestamp' (datetime).
			- Example rows:
				purchase      | price | category   | timestamp
				--------------------------------------------------------
				"laptop"      | 999.99| "electronics"| 2023
				"headphones"  | 199.99| "electronics"| 2023
		"""

		user_question = f"USER QUESTION:\n{question.strip()}"
		prior_context = f"KNOWN_RESULTS PREVIEW (read-only):\n{known_results_preview}"
  
		prompt = f"{system_instructions}\n\n{prior_context}\n\n{user_question}"
		code = ask_for_code(prompt)
  
		return code


	def execute_algorithm(self, code: str, known_results: Dict[str, Any]) -> Any:
		"""Execute the generated algorithm and return the result buffer."""

		return execute_snippet(code, user_data=self.data, known_results=known_results)


	def execute(self):
		"""Execute the entire knowledge graph from root to leaves,
		updating buffers along the way."""
		pass


	def close(self):
		self.graph.close()


# Mock user data
mock_data = pd.DataFrame({
	"purchase": ["laptop", "headphones", "coffee", "book"],
	"price": [999.99, 199.99, 4.99, 14.99],
	"category": ["electronics", "electronics", "groceries", "books"],
	"timestamp": pd.to_datetime(["2023-01-15", "2023-02-20", "2023-03-05", "2023-04-10"])
})

k_graph = KnowledgeGraph(user_data=mock_data)

k_graph.query("What is the total amount spent on electronics?")
k_graph.query("What is the total amount spend on electronics and books?")

k_graph.close()