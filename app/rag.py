from langchain_community.vectorstores import Chroma
from langchain_openai  import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter

retriever = None


def initialize_vectorstore():
    loader = TextLoader("book_summaries.txt", encoding="utf-8")
    documents = loader.load()

    text_splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=0
    )
    docs = text_splitter.split_documents(documents)

    embedding_function = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key="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")

    vectorstore = Chroma.from_documents(
        docs,
        embedding_function,
        persist_directory="chroma_books"
    )

    retriever = vectorstore.as_retriever()
    print("Vectorstore initialized and retriever created.")
    return retriever



def create_vectorstore(query, retriever):
    results = retriever.invoke(query)

    #for doc in results:
    #    print(doc.page_content)

    seen = set()
    unique_chunks = []
    for doc in results:
        text = doc.page_content.strip()
        if text not in seen:
            seen.add(text)
            unique_chunks.append(text)

    context = "\n\n".join(unique_chunks)

    prompt = f"""
    Folosind contextul de mai jos, răspunde conversațional (ca intr-o conversatie normala, cu interjectii si cuvinte de umplutura) la întrebarea utilizatorului.
    Daca raspunsul pe care vrei sa il dai nu se afla in cadrul contextului sau al conversației, raspunde cu "Nu am suficiente informatii pentru a raspunde la aceasta intrebare.".
    Daca intrebarea se refera la conversatie, poti sa ignori contextul.

    REGULĂ STRICTĂ: când decizi să folosești o funcție (tool), include OBLIGATORIU în `content` o propoziție scurtă în română care reia parametrii extrași din Conversație sau din Context (ex.: titlurile detectate) și, dacă e posibil, o citare foarte scurtă (≤20 cuvinte) din Context.
    Nu lăsa `content` gol. Nu inventa informații care nu există în Context.

    Context:
    {context}

    Conversație:
    {query}

    Răspuns:
    """
    print(prompt)
    return prompt
