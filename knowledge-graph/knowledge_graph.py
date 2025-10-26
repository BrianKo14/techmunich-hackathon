from weaviate_client import WeaviateGraph
from code_executor import execute_snippet
from openai_client import ask_for_code

import pandas as pd
from typing import Any

class KnowledgeGraph:
	def __init__(self, user_data):
		self.graph = WeaviateGraph()
		self.data = user_data

	def query(self, question: str):
		"""Use the available knowledge base to answer the question.
		Execute solution and create a new node with the answer.
		Connect the new node to relevant nodes in the knowledge base."""

		# relevant_nodes = self.find_relevant_nodes(question)	

		code = self.generate_algorithm(question)
		print("Generated Algorithm Code:")
		print(code)
		result_buffer = self.execute_algorithm(code)
  
		self.graph.insert_node(
			user_query=question,
			algorithm=code,
			buffer=str(result_buffer),
			parent_ids=[], # TODO: relevant_nodes
		)

		print("Knowledge Graph Nodes After Insertion:")
		self.graph.print_nodes()


	def find_relevant_nodes(self, question: str):
		"""Search knowledge base.
		Find the youngest node containing relevant information to the question
		(i.e. no descendants contain relevant information)."""
		
		if (self.graph.has_nodes() is False):
			return []

		return [] # TODO:

	def generate_algorithm(self, question: str) -> str:
		"""Generate an algorithm to answer the question based on relevant nodes and user data."""

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
  
		prompt = f"{system_instructions}\n\n{user_question}"
		code = ask_for_code(prompt)
  
		return code

	def execute_algorithm(self, code: str):
		"""Execute the generated algorithm and return the result buffer."""

		return execute_snippet(code, user_data=self.data)

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
k_graph.query("How many books were purchased?")

k_graph.close()