import os, weaviate
from weaviate.classes.init import Auth, AdditionalConfig, Timeout
from weaviate.classes.config import Configure, Property, DataType, ReferenceProperty

from typing import Any, Dict, List


class WeaviateGraph:
	def __init__(self):
		self.client, self.nodes = self.start_knowledge_graph()


	def start_knowledge_graph(self):

		# ---- 1. Start client

		client = weaviate.connect_to_weaviate_cloud(
			cluster_url = os.environ["WEAVIATE_URL"],
			auth_credentials = Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
			additional_config = AdditionalConfig(timeout=Timeout(init=10)),
			headers = { "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"] },
		)


		# ---- 2. Create node class
     
		# Safe reset
		if "Node" in client.collections.list_all():
			client.collections.delete("Node")


		# Create class
		client.collections.create(
			name="Node",
			vector_config = Configure.Vectors.text2vec_openai(
				source_properties=["user_query", "algorithm", "buffer"]
			),
			properties = [
				Property(name="user_query", data_type=DataType.TEXT),

				Property(name="algorithm", data_type=DataType.TEXT),	# AI-generated algorithm used to generate the node

				Property(name="buffer", data_type=DataType.TEXT),	# Buffered computed solution of the last execution
											# is a JSON containing e.g. number, string, matplotlib code.

				Property(name="summary", data_type=DataType.TEXT),	# Summary / variable name for browsing and coding convenience;
											# the AI may use this to reference the node buffer in future code generation.
			],
			references = [ReferenceProperty(name="parents", target_collection="Node")],
		)

		nodes = client.collections.use("Node")

		return client, nodes


	def has_nodes(self) -> bool:
		res = self.nodes.query.fetch_objects(limit=1)
		return bool(res.objects)


	def insert_node(self, user_query: str, algorithm: str, buffer: str, parent_ids: list[str], summary: str) -> str:
		node_id = self.nodes.data.insert({
			"user_query": user_query,
			"algorithm": algorithm,
			"buffer": buffer,
			"summary": summary
		}, references={
			"parents": parent_ids
		})
		return node_id

  
	def get_node(self, node_id: str):
		return self.nodes.query.fetch_object_by_id(
			uuid=node_id,
			include_vector=False
		)

  
	def get_algorithm(self, node_id: str) -> str:
		node = self.get_node(node_id)
		return node.properties["algorithm"]


	def get_variable(self, node_id: str) -> Dict[str, Any]:
		"""Maps node summary to its buffer content."""
  
		node = self.get_node(node_id)
		summary = node.properties.get("summary", f"node_{node_id.replace('-', '_')}")
		buffer = node.properties["buffer"]
		return {summary: buffer}

  
	def update_buffer(self, node_id: str, new_buffer: str):
		"""Used to update buffer data on re-execution of the node's algorithm."""
  
		self.nodes.data.update(
			uuid = node_id,
			properties = { "buffer": new_buffer }
		)
		return self.get_node(node_id)


	def print_nodes(self):
		node = self.client.collections.get("Node")
		for obj in node.query.fetch_objects(limit=5).objects:
			print(obj.properties)


	def close(self):
		self.client.close()