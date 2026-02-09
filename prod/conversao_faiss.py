from classe_faiss import Faiss
from bd import integracaoBD

faiss = Faiss()
bd = integracaoBD()

idMin = faiss.ret_checkpoint()

query = f"select id, embedding from embeddings_api where id>{idMin};"

resultado = bd.executaQuery(query=query)

faiss.cria_documento_apis(resultado)

query = f"select id, idApi, embedding from embeddings;"

resultado = bd.executaQuery(query=query)

faiss.cria_documento_endpoint(resultado)