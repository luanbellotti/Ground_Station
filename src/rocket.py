from stl import mesh
import numpy as np
import pyqtgraph.opengl as gl
from pathlib import Path

class Leitor_stl:
    def __init__(self, nome_arquivo="basic_rocket.stl"):
        # DEFINE O CAMINHO RELATIVO DO ARQUIVO
        pasta_atual = Path(__file__).parent
        self.caminho_arquivo = pasta_atual / ".." / "imgs" / nome_arquivo

    def carregar_foguete(self):
        try:
            # 1. LEITURA DO ARQUIVO STL
            minha_mesh = mesh.Mesh.from_file(str(self.caminho_arquivo))
            
            # 2. EXTRAÇÃO E VERIFICAÇÃO DOS DADOS
            pontos = minha_mesh.vectors.reshape(-1, 3)
            
            # 3. ENCONTRANDO O CENTRO GEOMÉTRICO DA PEÇA
            centro_x = np.mean(pontos[:, 0])
            centro_y = np.mean(pontos[:, 1])
            min_z = np.min(pontos[:, 2])

            # 4. ARRASTANDO TODOS OS TRIANGULOS PARA A ORIGEM
            pontos[:, 0] -= centro_x
            pontos[:, 1] -= centro_y
            pontos[:, 2] -= min_z

            pontos = pontos*2
            faces = np.arange(pontos.shape[0]).reshape(-1, 3)

            # Verificação de segurança: O arquivo está vazio?
            if pontos.size == 0:
                raise ValueError("O arquivo STL foi lido mas não contém triângulos (está vazio).")
            
            # 3. CRIAÇÃO EXPLÍCITA DO MESHDATA (A Correção Principal)
            # Criamos o objeto de dados antes. Isso garante que o PyQTGraph
            # calcule as normais e valide os dados antes de desenhar.
            dados_malha = gl.MeshData(vertexes=pontos, faces=faces)

            # 4. CRIAÇÃO DO OBJETO VISUAL
            mesh_item = gl.GLMeshItem(
                meshdata=dados_malha, # Passamos o objeto pronto
                smooth=True, 
                drawEdges=False,
                color=(1,0,0,1), 
                shader='balloon'
            )
            return mesh_item

        except Exception as e:
            print(f"ERRO AO CARREGAR STL ({e}) -> Usando cilindro padrão.")
            
            # FALLBACK: CILINDRO PADRÃO
            md = gl.MeshData.cylinder(rows=10, cols=20, radius=[2, 0], length=10)
            return gl.GLMeshItem(meshdata=md, smooth=True, color=(1, 0, 0, 1), shader='balloon')