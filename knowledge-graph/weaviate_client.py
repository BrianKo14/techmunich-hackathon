import os, weaviate
from weaviate.classes.init import Auth, AdditionalConfig, Timeout
from weaviate.classes.config import Configure, Property, DataType, ReferenceProperty


class WeaviateGraph:
	def __init__(self):
		self.client, self.nodes = self.start_knowledge_graph()


	def start_knowledge_graph(self):

		# ---- 1. Start client

		client = weaviate.connect_to_weaviate_cloud(
			cluster_url = os.environ["WEAVIATE_URL"],
			auth_credentials = Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
			additional_config = AdditionalConfig(timeout=Timeout(init=10)),
		)


		# ---- 2. Create node class
     
		# Safe reset
		if "Node" in client.collections.list_all():
			client.collections.delete("Node")


		client.collections.create(
			name="Node",
			# vector_config = Configure.Vectors.text2vec_openai(
			# 	source_properties=["user_query", "algorithm", "buffer"]
			# ),
			properties = [
				Property(name="user_query", data_type=DataType.TEXT),
				Property(name="algorithm", data_type=DataType.TEXT),	# AI-generated algorithm used to generate the node
				Property(name="buffer", data_type=DataType.TEXT),	# Buffered computed solution of the last execution
											# is a JSON containing e.g. number, string, matplotlib code
			],
			references = [ReferenceProperty(name="parents", target_collection="Node")],
		)

		nodes = client.collections.use("Node")

		return client, nodes

	def has_nodes(self) -> bool:
		res = self.nodes.query.fetch_objects(limit=1)
		return bool(res.objects)


	def insert_node(self, user_query: str, algorithm: str, buffer: str, parent_ids: list[str]) -> str:
		node_id = self.nodes.data.insert({
			"user_query": user_query,
			"algorithm": algorithm,
			"buffer": buffer,
		}, references={
			"parents": parent_ids
		})
		return node_id

	def print_nodes(self):
		node = self.client.collections.get("Node")
		for obj in node.query.fetch_objects(limit=5).objects:
			print(obj.properties)

	def close(self):
		self.client.close()

	