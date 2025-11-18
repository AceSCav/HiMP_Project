from docxtpl import DocxTemplate
from datetime import date
from Home_Page import crud_support
import os
import sys



documentos_info = {
    "Procuração - Representação Aima": {
        "arquivo": "Procuracao_Representacao_Aima.docx",
        "campos": [
            "nome", "nacionalidade", "naturalidade", "passaporte",
             "validade_passaporte", 
            "nif", "endereço", "data_documento", "nome_upper"
        ]
    },
    "Contrato de Prestaçao de Serviços Jurídicos- Ação Intimação": {
        "arquivo": "Contrato_de_Prestacao_de_Serviços_Jurídicos_Acao_Intimacao.docx",
        "campos": [
            "nome", "nacionalidade", "passaporte",
             "validade_passaporte",
            "nif", "endereço", "data_documento", "estado_civil", "valor_contrato", "numero_parcelas", "valor_contrato_div_parcelas"
        ]
    },
    "Procuração - Naturalização- Art.º 6.º, n.º 1": {
        "arquivo": "Procuracao_Naturalização_Art_6_n_1.docx",
        "campos": [
            "nome", "nacionalidade", "passaporte",
             "validade_passaporte", 
            "nif", "endereço", "data_documento", "titulo_residencia", "validade_titulo_residencia", "nome_upper", 
            "estado_civil"
        ]
    },
    "Procuração - Casamento - Art.º 3.º, n.º 1": {
        "arquivo": "Procuracao_Casamento_Art_3_n_1.docx",
        "campos": [
            "nome", "nacionalidade", "naturalidade", "endereço",
            "passaporte", "emissao_passaporte", "validade_passaporte",
            "local_emissao_passaporte", "data_documento", "nome_upper", "estado_civil"
        ]
    },
    "Procuração - Ação Intimação": {
        "arquivo": "Procuracao_Acao_Intimacao.docx",
        "campos": [
            "nome", "nacionalidade", "naturalidade", "passaporte",
             "validade_passaporte", 
            "nif", "data_documento", "endereço", "nome_upper"
        ]
    },
    "Procuração - Filho Originário - Art.º 1º CPR": {
        "arquivo": "Procuracao_Filho_Originário_Art_1_C.docx",
        "campos": [
            "nome", "nacionalidade", "naturalidade", "passaporte",
             "validade_passaporte", "emissao_passaporte", "local_emissao_passaporte",
            "data_documento", "endereço", "nome_upper", "estado_civil"
        ]
    },
    "Procuração - (mãe) - Netos de Portugueses - Art.º 1º D": {
        "arquivo": "Procuracao_mae_Netos_de_Portugueses_Art_1_D.docx",
        "campos": [
            "nome", "nacionalidade", "naturalidade", "passaporte",
             "validade_passaporte", "emissao_passaporte", "local_emissao_passaporte",
            "data_documento", "endereço", "nome_upper", "estado_civil"
        ]
    },
    "Procuração - (pai)  - Netos de Portugueses - Art.º 1º D": {
        "arquivo": "Procuracao_pai_Netos_de_Portugueses_Art_1_D.docx",
        "campos": [
            "nome", "nacionalidade", "naturalidade", "passaporte",
             "validade_passaporte", "emissao_passaporte", "local_emissao_passaporte",
            "data_documento", "endereço", "nome_upper", "estado_civil"
        ]
    },
    "Contrato de Prestação de Serviços Jurídicos - Nacionalidade": {
        "arquivo": "Contrato_de_Prestacao_de_Servicos_Juridicos_Nacionalidade.docx",
        "campos": [
            "nome", "nacionalidade", "valor_contrato", "numero_parcelas", "valor_contrato_div_parcelas", "valor_contrato_string", 
            "mes_ano_inicio_prestacao","data_documento", "endereço", "valor_contrato_div_parcelas_string"
        ]
    }
}



def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

base_path = resource_path("")

def gerar_documento(tipo_doc_combobox, dados):
    if tipo_doc_combobox not in documentos_info:
        raise ValueError(f"Documento '{tipo_doc_combobox}' não configurado.")

    info = documentos_info[tipo_doc_combobox]

    # Ajuste aqui para considerar a pasta dentro do bundle
    arquivo_path = resource_path(os.path.join("gerador_documentos", info["arquivo"]))

    doc = DocxTemplate(arquivo_path)

    campos_vazios = [campo for campo in info["campos"] if not dados.get(campo)]
    if campos_vazios:
        raise ValueError(
            "Os seguintes campos estão vazios ou não preenchidos:\n" + "\n".join(campos_vazios)
        )

    contexto = {campo: dados.get(campo, "") for campo in info["campos"]}

    doc.render(contexto)

    pasta_destino = os.path.join(os.path.expanduser("~"), "Desktop", "Documentos_Gerados")

    os.makedirs(pasta_destino, exist_ok=True)

    nome_arquivo = f"{tipo_doc_combobox.replace(' ', '_')}{contexto.get('nome', 'sem_nome')}.docx"
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)

    doc.save(caminho_completo)

    return caminho_completo