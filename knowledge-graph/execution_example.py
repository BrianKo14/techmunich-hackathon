
# You can run this example to see how the KnowledgeGraph processes user queries.

from knowledge_graph import KnowledgeGraph
import pandas as pd

# We create a mock dataset representing the user's raw financial data, which is the primary input to all queries.
# In production, we bind this to the auto-classified ledger that derives from contactless payments, bank statements, etc.
mock_data = pd.DataFrame({
	"purchase": ["laptop", "headphones", "coffee", "book"],
	"price": [999.99, 199.99, 4.99, 14.99],
	"category": ["electronics", "electronics", "groceries", "books"],
	"timestamp": pd.to_datetime(["2023-01-15", "2023-02-20", "2023-03-05", "2023-04-10"])
})

k_graph = KnowledgeGraph(user_data=mock_data)

# First example: simple query about spending.
query1 = "What is the total amount spent on electronics?"
answer1 = k_graph.query(query1)
print(f"Q: {query1}\nA: {answer1}\n")

# Second example: requires using known results from prior computations.
# We'll search through existing nodes to detect this relevant pre-computed data and provide it for the new computation.
query2 = "What is the total amount spent on electronics and books?"
answer2 = k_graph.query(query2)
print(f"Q: {query2}\nA: {answer2}\n")

k_graph.close()