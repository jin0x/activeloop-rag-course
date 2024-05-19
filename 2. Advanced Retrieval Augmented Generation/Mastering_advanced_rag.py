# -*- coding: utf-8 -*-
"""Module 02-Mastering Advanced RAG.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1VUGiJ_bHxnCD5a0xt6LPTpFJ4m26lyIC
"""

!pip install -q llama-index==0.9.14.post3 deeplake==3.8.8 openai==1.3.8 cohere==4.37

import os

os.environ['OPENAI_API_KEY'] = '<YOUR_OPENAI_API_KEY>'
os.environ['ACTIVELOOP_TOKEN'] = '<YOUR_ACTIVELOOP_API_KEY>'
os.environ['COHERE_API_KEY'] = '<YOUR_COHERE_API_KEY>'

!mkdir -p './paul_graham/'
!wget 'https://raw.githubusercontent.com/run-llama/llama_index/main/docs/examples/data/paul_graham/paul_graham_essay.txt' -O './paul_graham/paul_graham_essay.txt'

from llama_index import SimpleDirectoryReader

# load documents
documents = SimpleDirectoryReader("./paul_graham").load_data()

from llama_index import ServiceContext

# initialize service context (set chunk size)
service_context = ServiceContext.from_defaults(chunk_size=512, chunk_overlap=64)
node_parser = service_context.node_parser

nodes = node_parser.get_nodes_from_documents(documents)

from llama_index.vector_stores import DeepLakeVectorStore

my_activeloop_org_id = "genai360"
my_activeloop_dataset_name = "LlamaIndex_paulgraham_essay"
dataset_path = f"hub://{my_activeloop_org_id}/{my_activeloop_dataset_name}"

# Create an index over the documnts
vector_store = DeepLakeVectorStore(dataset_path=dataset_path, overwrite=False)

from llama_index.storage.storage_context import StorageContext

storage_context = StorageContext.from_defaults(vector_store=vector_store)
storage_context.docstore.add_documents(nodes)

from llama_index import VectorStoreIndex

vector_index = VectorStoreIndex(nodes, storage_context=storage_context)

query_engine = vector_index.as_query_engine(streaming=True, similarity_top_k=10)

streaming_response = query_engine.query(
    "What does Paul Graham do?",
)
streaming_response.print_response_stream()

"""# SubQuestion Query Engine"""

query_engine = vector_index.as_query_engine(similarity_top_k=10)

from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine

query_engine_tools = [
    QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="pg_essay",
            description="Paul Graham essay on What I Worked On",
        ),
    ),
]

query_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=query_engine_tools,
    service_context=service_context,
    use_async=True,
)

response = query_engine.query(
    "How was Paul Grahams life different before, during, and after YC?"
)

print( ">>> The final response:\n", response )

"""# Cohere Rerank"""

import cohere

# Get your cohere API key on: www.cohere.com
co = cohere.Client(os.environ['COHERE_API_KEY'])

# Example query and passages
query = "What is the capital of the United States?"
documents = [
   "Carson City is the capital city of the American state of Nevada. At the  2010 United States Census, Carson City had a population of 55,274.",
   "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean that are a political division controlled by the United States. Its capital is Saipan.",
   "Charlotte Amalie is the capital and largest city of the United States Virgin Islands. It has about 20,000 people. The city is on the island of Saint Thomas.",
   "Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district. ",
   "Capital punishment (the death penalty) has existed in the United States since before the United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.",
   "North Dakota is a state in the United States. 672,591 people lived in North Dakota in the year 2010. The capital and seat of government is Bismarck."
   ]

results = co.rerank(query=query, documents=documents, top_n=3, model='rerank-english-v2.0') # Change top_n to change the number of results returned. If top_n is not passed, all results will be returned.

for idx, r in enumerate(results):
  print(f"Document Rank: {idx + 1}, Document Index: {r.index}")
  print(f"Document: {r.document['text']}")
  print(f"Relevance Score: {r.relevance_score:.2f}")
  print("\n")

"""# Cohere in LlamaIndex"""

import os
from llama_index.postprocessor.cohere_rerank import CohereRerank


cohere_rerank = CohereRerank(api_key=os.environ['COHERE_API_KEY'], top_n=2)

query_engine = vector_index.as_query_engine(
    similarity_top_k=10,
    node_postprocessors=[cohere_rerank],
)

response = query_engine.query(
    "What did Sam Altman do in this essay?",
)
print( response )



