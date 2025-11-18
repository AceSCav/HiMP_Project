import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.constants import *
from database import supabase
from Home_Page import pagina
from tkinter import messagebox
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, root_validator
from typing import Optional, Literal
from datetime import date
import re
from collections import defaultdict
from datetime import datetime
### INDEX:
# 1 - READ FUNCTIONS
# 2 - VALIDATION FUNCTIONS
# 3 - CREATE FUNCTIONS
# 4 - UPDATE FUNCTIONS
# 5 - DELETE FUNCTIONS



##################################################################################################
##################################################################################################
####################################### 1 - READ FUNCTIONS #######################################
##################################################################################################
##################################################################################################


def search_tree_result(name_search_box=None, nif_search_box=None, passport_search=None, bi_cc_search_box=None, number_of_process_search_box=None):
    try:
        # Obter os valores das entradas
        name = name_search_box.get() if name_search_box else None
        nif = nif_search_box.get().strip() if nif_search_box else None
        passport = passport_search.get().upper().strip() if passport_search else None
        bi_cc_titulo_residência = bi_cc_search_box.get().strip().upper() if bi_cc_search_box else None
        number_of_process = number_of_process_search_box.get().strip().upper() if number_of_process_search_box else None
        # Contar quantos parâmetros foram fornecidos
        params = [name, nif, passport, bi_cc_titulo_residência, number_of_process]
        provided_params = [param for param in params if param is not None and param != ""]
        # Verificar se mais de um parâmetro foi fornecido
        if len(provided_params) > 1:
            messagebox.showerror("Erro de Pesquisa", "Por favor, forneça apenas um parâmetro para pesquisa de cada vez.")
            return None
        # Verificar se nenhum parâmetro foi fornecido
        if not provided_params:
            messagebox.showerror("Erro de Pesquisa", "Nenhum parâmetro válido fornecido para pesquisa.")
            return None
        # Executar a consulta apropriada
        if number_of_process:
            # Busca pelo número do processo associado ao cliente
            process_response = (supabase.table("processo").select("cliente_id").ilike("numero_processo", f"%{number_of_process}%").execute())
            cliente_id = [item["cliente_id"] for item in process_response.data]
            if cliente_id:
                response = supabase.table("cliente").select("*").in_("cliente_id", cliente_id).execute()
            else:
                messagebox.showinfo("Sem Resultados", "Nenhum cliente encontrado para o número do processo fornecido.")
                return None
        else:
            # Busca normal na tabela cliente
            column_name = "nome_completo" if name else "nif" if nif else "passaporte" if passport else "bi_cc_titulo_residência"
            value = name if name else nif if nif else passport if passport else bi_cc_titulo_residência
            response = supabase.table("cliente").select("*").ilike(column_name, f"%{value}%").execute()
        if not response.data:
            messagebox.showinfo("Sem Resultados", "Nenhum resultado encontrado para os critérios de pesquisa.")
            return None
        return response.data
    except Exception as e:
        messagebox.showerror("Erro no Sistema", f"Ocorreu um erro durante a pesquisa:\n{str(e)}")
        return None

def select_client_by_nif_passport(nif_search_box_for_contract=None, passport_search_box_for_contract=None):
    nif = nif_search_box_for_contract.get()
    passport = passport_search_box_for_contract.get()
    params = [nif, passport]
    provided_params = [param for param in params if param is not None and param != ""]
    if len(provided_params) > 1:
            messagebox.showerror("Erro de Pesquisa", "Por favor, forneça apenas um parâmetro para pesquisa de cada vez.")
            return None
    if not provided_params:
            messagebox.showerror("Erro de Pesquisa", "Nenhum parâmetro válido fornecido para pesquisa.")
            return None
    try:
        column_name = "nif" if nif else "passaporte"
        value = nif if nif else passport
        response = supabase.table("cliente").select("*").ilike(column_name, f"%{value}%").execute()
        if not response.data:
            messagebox.showinfo("Sem Resultados", "Nenhum resultado encontrado para os critérios de pesquisa.")
            return None
        return response.data
    except Exception as e:
        messagebox.showerror("Erro no Sistema", f"Ocorreu um erro durante a pesquisa:\n{str(e)}")
        return None


def select_client_by_id(client_id):
    try:
        response = supabase.table("cliente").select("*").eq("cliente_id", client_id).execute()
        if response.data:
            return response.data[0]
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum cliente encontrado com o ID fornecido.")
            return None
    except Exception as e:
        messagebox.showerror("Erro no Sistema", f"Ocorreu um erro ao buscar o cliente:\n{str(e)}")
        return None
    



def search_processes_by_client_id(client_id):
    try:
        response = supabase.table("processo")\
            .select("*, entidade (entidade), tipo_do_processo (tipo_do_processo)")\
            .eq("cliente_id", client_id)\
            .execute()
        
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum processo encontrado para o cliente fornecido.")
            return None
    except Exception as e:
        return None
    
def select_process_by_process_id(processo_id):
    try:
        response = supabase.table("processo")\
            .select("*, entidade (entidade), tipo_do_processo (tipo_do_processo)")\
            .eq("processo_id", processo_id)\
            .execute()
        
        if response.data:
            return response.data[0]
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum processo encontrado com o ID fornecido.")
            return None
    except Exception as e:
        return None


def select_list_of_steps_by_process_id(processo_id):
    try:
        response = supabase.table("etapa_processo")\
            .select("*, lista_fases_processo (fase)")\
            .eq("processo_id", processo_id)\
            .execute()
        
        if response.data:
            return response.data
        else:
            return None
    except Exception as e:
        return None

def select_process_step_by_step_id(etapa_id):
    try:
        response = supabase.table("etapa_processo")\
            .select("*, lista_fases_processo (fase)")\
            .eq("etapa_id", etapa_id)\
            .execute()
        
        if response.data[0]:
            return response.data[0]
        else:
            return None
    except Exception as e:
        return None

def select_list_of_process_step():
    try:
        response = supabase.table("lista_fases_processo").select("*").execute()
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhuma etapa de processo encontrada.")
            return None
    except Exception as e:
        return None
    
def select_list_of_court():
    try:
        response = supabase.table("tipo_do_processo").select("*").execute()
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum tipo_do_processo encontrado.")
            return None
    except Exception as e:
        return None

def select_list_of_type_process():
    try:
        response = supabase.table("entidade").select("*").execute()
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum tipo_do_processo encontrado.")
            return None
    except Exception as e:
        return None

def select_list_of_reason_payment():
    try:
        response = supabase.table("motivo").select("*").execute()
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum motivo de pagamento encontrado.")
            return None
    except Exception as e:
        return None
    
def select_list_of_state_payment():
    try:
        response = supabase.table("status_pagamento").select("*").execute()
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum estado de pagamento encontrado.")
            return None
    except Exception as e:
        return None

def select_all_payments():
    try:
        # Puxa os dados da tabela pagamento + dados do cliente relacionado
        response = supabase.table("pagamento")\
            .select("*, cliente(nome_completo)")\
            .execute()

        if response.data:
            return response.data
        else:
            return None
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar pagamentos: {e}")
        return None


def select_list_of_payments(cliente_id):
    try:
        response = supabase.table("pagamento")\
            .select("*, status_pagamento (status), motivo (motivo)")\
            .eq("cliente_id", cliente_id)\
            .execute()
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum estado de pagamento encontrado.")
            return None
    except Exception as e:
        return None
    
def select_payment_by_payment_id(pagamento_id):
    try:
        response = supabase.table("pagamento")\
            .select("*, status_pagamento (status), motivo (motivo)")\
            .eq("pagamento_id", pagamento_id)\
            .execute()
        if response.data[0]:
            return response.data[0]
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum estado de pagamento encontrado.")
            return None
    except Exception as e:
        return None
    
def select_clients_by_process_step(step):
    try:

        etapas_pendentes = supabase.table("etapa_processo")\
            .select("processo_id, data_fase, observação, fase_id, etapa_id")\
            .eq("fase_id", step)\
            .execute().data

        if not etapas_pendentes:
            return []

        processo_ids = list({etapa["processo_id"] for etapa in etapas_pendentes})

        # Agora busca TODAS as etapas desses processos
        todas_etapas = supabase.table("etapa_processo")\
            .select("processo_id, data_fase, etapa_id, fase_id")\
            .in_("processo_id", processo_ids)\
            .order("data_fase")\
            .execute().data


        # Agrupar todas as etapas por processo


        etapas_por_processo = defaultdict(list)
        for etapa in todas_etapas:
            etapas_por_processo[etapa["processo_id"]].append(etapa)


        # Filtrar processos que têm "Processo em Trâmite" como última etapa
        processos_pendentes = []
        for etapa_pendente in etapas_pendentes:
            processo_id = etapa_pendente["processo_id"]
            etapa_id_pendente = etapa_pendente["etapa_id"]

            outras_etapas = etapas_por_processo[processo_id]
            existe_etapa_posterior = any(
                outra["etapa_id"] > etapa_id_pendente for outra in outras_etapas
            )

            if not existe_etapa_posterior:
                processos_pendentes.append(etapa_pendente)

        if not processos_pendentes:
            return []

        # Buscar os dados dos processos correspondentes
        processos_result = supabase.table("processo")\
            .select("processo_id, cliente_id, entidade_id")\
            .in_("processo_id", [p["processo_id"] for p in processos_pendentes])\
            .execute()
        
        

        # Buscar os dados dos clientes
        cliente_ids = list({p["cliente_id"] for p in processos_result.data})
        clientes_result = supabase.table("cliente")\
            .select("cliente_id, nome_completo")\
            .in_("cliente_id", cliente_ids)\
            .execute()

        cliente_map = {
            c["cliente_id"]: c["nome_completo"]
            for c in clientes_result.data
        }

        processo_map = {
            p["processo_id"]: {
                "cliente_id": p["cliente_id"],
                "entidade_id": p["entidade_id"]
            }
            for p in processos_result.data
        }

        tipo_ids = list({
            p["entidade_id"]
            for p in processos_result.data
            if p["entidade_id"] is not None
        })

        if tipo_ids:
            tipos_result = supabase.table("entidade")\
                .select("entidade_id, entidade")\
                .in_("entidade_id", tipo_ids)\
                .execute()

            tipo_map = {
                t["entidade_id"]: t["entidade"]
                for t in tipos_result.data
            }
        else:
            tipo_map = {}

        # Montar resultado final
        fase_ids = list({etapa["fase_id"] for etapa in processos_pendentes})
        fases_result = supabase.table("lista_fases_processo")\
            .select("fase_id, fase")\
            .in_("fase_id", fase_ids)\
            .execute()

        fase_map = {
            f["fase_id"]: f["fase"]
            for f in fases_result.data
        }
        resultado = []
        for etapa in processos_pendentes:
            processo = processo_map.get(etapa["processo_id"])
            if processo:
                tipo_nome = tipo_map.get(processo["entidade_id"], "Desconhecido")
                cliente_id = processo["cliente_id"]
                resultado.append({
                    "cliente_id": cliente_id,
                    "nome_completo": cliente_map.get(cliente_id, "Desconhecido"),
                    "data_fase": etapa.get("data_fase"),
                    "observação": etapa.get("observação"),
                    "entidade": tipo_nome,
                    "processo_id": etapa["processo_id"],
                    "fase": fase_map.get(etapa["fase_id"], "Desconhecida")
                })


        return resultado

    except Exception as e:
        print("Erro ao buscar processos em trâmite:", e)
        return []

def select_all_calendar_events():
    try:
        response = supabase.table("agendamento")\
            .select("*, cliente (nome_completo)")\
            .execute()
        
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum evento encontrado.")
            return None
    except Exception as e:
        messagebox.showerror("Erro no Sistema", f"Ocorreu um erro ao buscar os eventos:\n{str(e)}")
        return None

def select_calendar_events_by_client_id(client_id):
    try:
        response = supabase.table("agendamento")\
            .select("*")\
            .eq("cliente_id", client_id)\
            .execute()
        
        if response.data:
            return response.data
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum evento encontrado para o cliente fornecido.")
            return None
    except Exception as e:
        messagebox.showerror("Erro no Sistema", f"Ocorreu um erro ao buscar os eventos:\n{str(e)}")
        return None

def select_calendar_event_by_event_id(event_id):
    try:
        response = supabase.table("agendamento")\
            .select("*")\
            .eq("evento_id", event_id)\
            .execute()
        
        if response.data:
            return response.data[0]
        else:
            messagebox.showinfo("Sem Resultados", "Nenhum evento encontrado com o ID fornecido.")
            return None
    except Exception as e:
        messagebox.showerror("Erro no Sistema", f"Ocorreu um erro ao buscar o evento:\n{str(e)}")
        return None


    

##################################################################################################
##################################################################################################
####################################### 1 - VALIDATION FUNCTIONS #################################
##################################################################################################
##################################################################################################

class ClienteInput(BaseModel):
    nome_completo: Optional[str] = Field(None, min_length=2, max_length=100)
    nif: Optional[str] = Field(None, pattern=r'^\d{9}$')
    niss: Optional[str] = Field(None, pattern=r'^\d{11}$')
    bi_cc_titulo_residência: Optional[str] = Field(None, min_length=5, max_length=50)
    
    validade_dia_bi: Optional[int] = Field(None, ge=1, le=31)
    validade_mes_bi: Optional[str] = Field(None)
    validade_ano_bi: Optional[int] = Field(None, ge=1900, le=2100)
    validade_bi_cc: Optional[str] = Field(None)  
    
    nascimento_dia: Optional[int] = Field(None, ge=1, le=31)
    nascimento_mes: Optional[str] = Field(None)
    nascimento_ano: Optional[int] = Field(None, ge=1900, le=2100)
    data_nascimento: Optional[str] = Field(None)

    estado_civil: Optional[str] = Field(None, min_length=5, max_length=50)
    
    passaporte: Optional[str] = Field(None, min_length=5, max_length=50, pattern=r'^[A-Za-z0-9]+$')
    validade_dia_passaporte: Optional[int] = Field(None, ge=1, le=31)
    validade_mes_passaporte: Optional[str] = Field(None)
    validade_ano_passaporte: Optional[int] = Field(None, ge=1900, le=2100)
    validade_passaporte: Optional[str] = Field(None) 
    local_emissão_passaporte: Optional[str] = Field(None) 

    emissao_dia_passaporte: Optional[int] = Field(None, ge=1, le=31)
    emissao_mes_passaporte: Optional[str] = Field(None)
    emissao_ano_passaporte: Optional[int] = Field(None, ge=1900, le=2100)
    emissão_passaporte: Optional[str] = Field(None) 

    emissao_dia_bi: Optional[int] = Field(None, ge=1, le=31)
    emissao_mes_bi: Optional[str] = Field(None)
    emissao_ano_bi: Optional[int] = Field(None, ge=1900, le=2100)
    emissão_bi_cc: Optional[str] = Field(None)

    rua: Optional[str] = Field(None, min_length=3, max_length=200)
    numero_rua: Optional[str] = Field(None,min_length=1, max_length=20)
    complemento: Optional[str] = Field(None,min_length=1, max_length=100)
    localidade: Optional[str] = Field(None, min_length=2, max_length=100)
    postal_code_1: Optional[str] = Field(None,min_length=1, max_length=10)
    postal_code_2: Optional[str] = Field(None,min_length=1, max_length=10)
    código_postal: Optional[str] = None
    
    email: Optional[EmailStr] = None
    ddi: Optional[int] = Field(None, ge=0, le=999)
    contato: Optional[str] = Field(None,max_length=20,pattern=r'^\d{1,20}$')
    profissão: Optional[str] = Field(None, max_length=50)
    nacionalidade: Optional[str] = Field(None, max_length=50)
    naturalidade: Optional[str] = Field(None, max_length=50)

    notas_documento: Optional[str] = Field(None, max_length=500)

    genero_masculino: Optional[bool] = Field(None)
    genero_feminino: Optional[bool] = Field(None)
    gênero: Optional[str] = None

    @field_validator('passaporte', 'bi_cc_titulo_residência')
    def upper_fields(cls, v):
        return v.upper() if v else v

    @field_validator('validade_mes_bi', 'validade_mes_passaporte', 'nascimento_mes', 'emissao_mes_passaporte', 'emissao_mes_bi')
    def validar_mes(cls, v):
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        if v is not None and v not in meses:
            raise ValueError(f'Mês deve ser um dos: {", ".join(meses)}')
        return v

    @field_validator('nome_completo', 'rua', 'complemento', 'localidade', 'profissão', 'nacionalidade', 'nacionalidade', 'local_emissão_passaporte')
    def inicial_maiusculo(cls, v):
        return v.title() if v else v
    
    @model_validator(mode='after')
    def montar_codigo_postal(cls, model):
        p1 = model.postal_code_1 or ''
        p2 = model.postal_code_2 or ''

        if p1 and p2:
            codigo = f"{p1}-{p2}"
        else:
            codigo = p1 or p2 or None
        
        model.código_postal = codigo
        
        if 'postal_code_1' in model.__dict__:
            del model.__dict__['postal_code_1']
        if 'postal_code_2' in model.__dict__:
            del model.__dict__['postal_code_2']
        
        return model
    @model_validator(mode='after')
    def montar_datas(cls, values):
        def montar_data(dia: Optional[int], mes_nome: Optional[str], ano: Optional[int]) -> Optional[str]:
            if dia and mes_nome and ano:
                nome_to_numero = {
                    'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
                    'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
                    'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
                }
                mes_num = nome_to_numero.get(mes_nome)
                if mes_num is None:
                    raise ValueError(f"Mês inválido: {mes_nome}")
                try:
                    return f'{ano}-{mes_num:02d}-{dia:02d}'
                except ValueError:
                    raise ValueError(f"Data inválida: {dia}/{mes_nome}/{ano}")
            return None

        values.validade_passaporte = montar_data(
            values.validade_dia_passaporte,
            values.validade_mes_passaporte,
            values.validade_ano_passaporte
        )
        values.emissão_passaporte = montar_data(
            values.emissao_dia_passaporte,
            values.emissao_mes_passaporte,
            values.emissao_ano_passaporte
        )
        values.data_nascimento = montar_data(
            values.nascimento_dia,
            values.nascimento_mes,
            values.nascimento_ano
        )
        values.validade_bi_cc = montar_data(
            values.validade_dia_bi,
            values.validade_mes_bi,
            values.validade_ano_bi
        )
        values.emissão_bi_cc = montar_data(
            values.emissao_dia_bi,
            values.emissao_mes_bi,
            values.emissao_ano_bi
        )

        for campo in [
            'validade_dia_passaporte', 'validade_mes_passaporte', 'validade_ano_passaporte',
            'emissao_dia_passaporte', 'emissao_mes_passaporte', 'emissao_ano_passaporte',
            'nascimento_dia', 'nascimento_mes', 'nascimento_ano',
            'validade_dia_bi', 'validade_mes_bi','validade_ano_bi', 'emissao_dia_bi', 'emissao_mes_bi', 'emissao_ano_bi'
        ]:
            if hasattr(values, campo):
                delattr(values, campo)

        return values
    
    @model_validator(mode='after')
    def check_genero(cls, values):
        masc = values.genero_masculino
        fem = values.genero_feminino

        if masc is not None or fem is not None:
            if masc and fem:
                raise ValueError("Só pode selecionar masculino ou feminino, não ambos.")
            
            if masc:
                values.gênero = "Masculino"
            elif fem:
                values.gênero = "Feminino"

            # Remove os campos temporários após uso
            for campo in ['genero_masculino', 'genero_feminino']:
                if hasattr(values, campo):
                    delattr(values, campo)

        return values
    
class ProcessInput(BaseModel):
    numero_processo: Optional[str] = Field(None, min_length=2, max_length=100)
    entidade_nome: Optional[str] = Field(None, min_length=2, max_length=100)
    tipo_do_processo_nome: Optional[str] = Field(None, min_length=2, max_length=100)
    juiz: Optional[str] = Field(None, min_length=2, max_length=100)
    processo_anexo_principal: Optional[str] = Field(None, min_length=2, max_length=100)
    cliente_id: int

    entidade_id: Optional[int] = None
    tipo_do_processo_id: Optional[int] = None

    @model_validator(mode='after')
    def convert_names_to_ids(cls, values):
        tipo_nome = values.entidade_nome
        tipo_do_processo_nome = values.tipo_do_processo_nome

        if tipo_nome is not None:
            tipos = select_list_of_type_process()
            for tipo in tipos:
                if tipo['entidade'] == tipo_nome:
                    values.entidade_id = tipo['entidade_id']
                    break
            else:
                raise ValueError(f"Tipo de processo inválido: {tipo_nome}")

        if tipo_do_processo_nome is not None:
            tribunais = select_list_of_court()
            for tipo_do_processo in tribunais:
                if tipo_do_processo['tipo_do_processo'] == tipo_do_processo_nome:
                    values.tipo_do_processo_id = tipo_do_processo['tipo_do_processo_id']
                    break
            else:
                raise ValueError(f"tipo_do_processo inválido: {tipo_do_processo_nome}")

        # Remove os campos de nome para não enviar ao Supabase
        if hasattr(values, 'entidade_nome'):
            delattr(values, 'entidade_nome')
        if hasattr(values, 'tipo_do_processo_nome'):
            delattr(values, 'tipo_do_processo_nome')
        return values

class PaymentInput(BaseModel):
    entidade: Optional[int] = Field(None)
    referencia: Optional[int] = Field(None)
    montante: Optional[float] = Field(None)
    data_limite_dia: Optional[int] = Field(None, ge=1, le=31)
    data_limite_mes: Optional[str] = Field(None)
    data_limite_ano: Optional[int] = Field(None, ge=1900, le=2100)
    data_limite: Optional[str] = Field(None)
    data_conclusao_dia: Optional[int] = Field(None, ge=1, le=31)
    data_conclusao_mes: Optional[str] = Field(None)
    data_conclusao_ano: Optional[int] = Field(None, ge=1900, le=2100)
    data_conclusao: Optional[str] = Field(None)
    motivo_nome: Optional[str] = Field(None, min_length=2, max_length=100)
    status_nome: Optional[str] = Field(None, min_length=2, max_length=100)
    motivo_id: Optional[int] = None
    status_id: Optional[int] = None
    cliente_id: int

    @field_validator("montante", mode="before")
    def converter_virgula_para_ponto(cls, v):
        if isinstance(v, str):
            v = v.replace(",", ".")
        try:
            return float(v)
        except:
            raise ValueError("Montante inválido: use ponto ou vírgula como separador decimal.")

    @model_validator(mode='after')
    def convert_names_to_ids(cls, values):
        motivo_nome = getattr(values, "motivo_nome", None)
        status_nome = getattr(values, "status_nome", None)

        if motivo_nome is not None:
            motivos = select_list_of_reason_payment()
            for motivo in motivos:
                if motivo['motivo'] == motivo_nome:
                    setattr(values, "motivo_id", motivo['motivo_id'])
                    break
            else:
                raise ValueError(f"Motivo inválido: {motivo_nome}")

        if status_nome is not None:
            status_list = select_list_of_state_payment()
            for status in status_list:
                if status['status'] == status_nome:
                    setattr(values, "status_id", status['status_id'])
                    break
            else:
                raise ValueError(f"Status inválido: {status_nome}")

        # Remover os nomes (não necessários no DB)
        if hasattr(values, "motivo_nome"):
            delattr(values, "motivo_nome")
        if hasattr(values, "status_nome"):
            delattr(values, "status_nome")
        return values


    @model_validator(mode='after')
    def montar_datas(cls, values):
        def montar_data(dia: Optional[int], mes_nome: Optional[str], ano: Optional[int]) -> Optional[str]:
            if dia and mes_nome and ano:
                nome_to_numero = {
                    'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
                    'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
                    'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
                }
                mes_num = nome_to_numero.get(mes_nome)
                if mes_num is None:
                    raise ValueError(f"Mês inválido: {mes_nome}")
                try:
                    return f'{ano}-{mes_num:02d}-{dia:02d}'
                except ValueError:
                    raise ValueError(f"Data inválida: {dia}/{mes_nome}/{ano}")
            return None

        values.data_conclusao = montar_data(
            values.data_conclusao_dia,
            values.data_conclusao_mes,
            values.data_conclusao_ano
        )
        values.data_limite = montar_data(
            values.data_limite_dia,
            values.data_limite_mes,
            values.data_limite_ano
        )

        for campo in [
            'data_conclusao_dia', 'data_conclusao_mes', 'data_conclusao_ano',
            'data_limite_dia', 'data_limite_mes', 'data_limite_ano',
        ]:
            if hasattr(values, campo):
                delattr(values, campo)
        return values
    
class EventInput(BaseModel):
    cliente_id: int
    titulo: Optional[str] = Field(None, min_length=2, max_length=100)
    data_evento_dia: Optional[int] = Field(None, ge=1, le=31)
    data_evento_mes: Optional[str] = Field(None)
    data_evento_ano: Optional[int] = Field(None, ge=1900, le=2100)
    hora_evento: Optional[str] = Field(None, pattern=r'^(0[0-9]|1[0-9]|2[0-3])$')  
    minuto_evento: Optional[str] = Field(None, pattern=r'^[0-5][0-9]$')             
    descricao: Optional[str] = Field(None, max_length=500)
    duracao: Optional[str] = Field(None, max_length=100)
    motivo: Optional[str] = Field(None, max_length=100)
    data_inicio : Optional[str] = Field(None)
    google_event_id: Optional[str] = Field(None, max_length=100)
    
    @field_validator('titulo')
    def inicial_maiusculo(cls, v):
        return v.title() if v else v

    @model_validator(mode='after')
    def montar_data_evento(cls, values):
        dia = values.data_evento_dia
        mes_nome = values.data_evento_mes
        ano = values.data_evento_ano
        hora = values.hora_evento or "00"
        minuto = values.minuto_evento or "00"

        if dia and mes_nome and ano:
            nome_to_numero = {
                'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
                'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
                'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
            }
            mes_num = nome_to_numero.get(mes_nome)
            if mes_num is None:
                raise ValueError(f"Mês inválido: {mes_nome}")
            try:
                dt = datetime(
                    year=ano, 
                    month=mes_num, 
                    day=dia, 
                    hour=int(hora), 
                    minute=int(minuto)
                )
                values.data_inicio = dt.isoformat()  
            except ValueError:
                raise ValueError(f"Data/hora inválida: {dia}/{mes_nome}/{ano} {hora}:{minuto}")

        # Limpar os campos temporários
        for campo in ['data_evento_dia', 'data_evento_mes', 'data_evento_ano', 'hora_evento', 'minuto_evento']:
            if hasattr(values, campo):
                delattr(values, campo)

        return values
    

##################################################################################################
##################################################################################################
####################################### 1 - CREATE FUNCTIONS #####################################
##################################################################################################
##################################################################################################
def create_client(data):
    try:
        response = supabase.table("cliente").insert(data).execute()

        return response.data
    except Exception as e:
        print("Erro ao inserir cliente no Supabase:", e)
        raise

def create_process(data):
    try:
        response = supabase.table("processo").insert(data).execute()

        return response.data
    except Exception as e:
        print("Erro ao inserir processo no Supabase:", e)
        raise

def create_step(data):
    try:
        response = supabase.table("etapa_processo").insert(data).execute()

        return response.data
    except Exception as e:
        print("Erro ao inserir etapa do processo no Supabase:", e)
        raise

def create_payment(data):
    try:
        response = supabase.table("pagamento").insert(data).execute()

        return response.data
    except Exception as e:
        print("Erro ao inserir pagamento no Supabase:", e)
        raise

def create_calendar_event(data):
    try:
        response = supabase.table("agendamento").insert(data).execute()
        return response.data
    except Exception as e:
        print("Erro ao inserir evento no calendário no Supabase:", e)
        raise
##################################################################################################
##################################################################################################
####################################### 1 - UPDATE FUNCTIONS #####################################
##################################################################################################
##################################################################################################
def update_client(client_id, data):
    try:
        response = supabase.table("cliente").update(data).eq("cliente_id", client_id).execute()

        return response.data
    except Exception as e:
        print("Erro ao atualizar cliente no Supabase:", e)
        raise

def update_process(process_id, data):
    try:
        response = supabase.table("processo").update(data).eq("processo_id", process_id).execute()

        return response.data
    except Exception as e:
        print("Erro ao atualizar processo no Supabase:", e)
        raise

def update_step(step_id, data):
    try:
        response = supabase.table("etapa_processo").update(data).eq("etapa_id", step_id).execute()

        return response.data
    except Exception as e:
        print("Erro ao atualizar etapa no Supabase:", e)
        raise

def update_payment(payment_id, data):
    try:
        response = supabase.table("pagamento").update(data).eq("pagamento_id", payment_id).execute()

        return response.data
    except Exception as e:
        print("Erro ao atualizar etapa no Supabase:", e)
        raise

def update_calendar_event(event_id, data):
    try:
        response = supabase.table("agendamento").update(data).eq("evento_id", event_id).execute()
        return response.data
    except Exception as e:
        print("Erro ao atualizar evento no calendário no Supabase:", e)
        raise
    
##################################################################################################
##################################################################################################
####################################### 1 - DELETE FUNCTIONS #####################################
##################################################################################################
##################################################################################################
def delete_process(processo_id):
    try:
        supabase.table("etapa_processo").delete().eq("processo_id", processo_id).execute()
        supabase.table("processo").delete().eq("processo_id", processo_id).execute()

        return True

    except Exception as e:
        print(f"Erro ao deletar processo {processo_id}: {e}")
        raise

def delete_step(etapa_id):
    try:
        response = supabase.table("etapa_processo").delete().eq("etapa_id", etapa_id).execute()

        return response.data
    except Exception as e:
        print("Erro ao deletar etapa no Supabase:", e)
        raise

def delete_payment(pagamento_id):
    try:
        response = supabase.table("pagamento").delete().eq("pagamento_id", pagamento_id).execute()

        return response.data
    except Exception as e:
        print("Erro ao deletar etapa no Supabase:", e)
        raise

def delete_calendar_event(event_id):
    try:
        response = supabase.table("agendamento").delete().eq("evento_id", event_id).execute()

        return response.data
    except Exception as e:
        print("Erro ao deletar evento no calendário no Supabase:", e)
        raise

######## SAVE AND LOAD PARA O CHECK LIST DE DOCUMENTOS ########
def save_client_documents(cliente_id, documentos_estados):
    # Busca documentos existentes para o cliente
    response = supabase.table("documentos_cliente")\
        .select("documento_nome")\
        .eq("cliente_id", cliente_id)\
        .execute()

    existentes = {item['documento_nome'] for item in response.data} if response.data else set()

    for doc_nome, entregue in documentos_estados.items():
        if doc_nome in existentes:
            supabase.table("documentos_cliente")\
                .update({"entregue": entregue})\
                .eq("cliente_id", cliente_id)\
                .eq("documento_nome", doc_nome)\
                .execute()
        else:
            supabase.table("documentos_cliente")\
                .insert({
                    "cliente_id": cliente_id,
                    "documento_nome": doc_nome,
                    "entregue": entregue
                }).execute()


    
def get_client_documents(cliente_id):
    response = supabase.table("documentos_cliente")\
        .select("documento_nome, entregue")\
        .eq("cliente_id", cliente_id)\
        .execute()

    if response.data:
        return {item['documento_nome']: item['entregue'] for item in response.data}
    else:
        return {}
    
##################################################################################################
##################################################################################################
####################################### 1 - UTILITARIES FUNCTIONS #####################################
##################################################################################################
##################################################################################################


def month_to_string(month):
		months_list = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
					   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
		if 1 <= month <= 12:
			return str(months_list[month - 1])
		else:
			return None


def open_whatsapp(number):
    try:
        import webbrowser
        webbrowser.open(f"https://wa.me/{number}")
    except Exception as e:
        messagebox.showerror("Erro ao Abrir WhatsApp", f"Ocorreu um erro ao tentar abrir o WhatsApp:\n{str(e)}")

def parse_datetime(datetime_str):
    if not datetime_str:
        return {"ano": "", "mes": "", "dia": "", "hora": "", "minuto": ""}
    try:
        date_part, time_part = datetime_str.split("T")
        year, month, day = map(int, date_part.split("-"))
        hour, minute, _ = map(int, time_part.split(":"))
        return {
            "ano": year,
            "mes": month,
            "dia": day,
            "hora": hour,
            "minuto": minute
        }
    except Exception:
        return {"ano": "", "mes": "", "dia": "", "hora": "", "minuto": ""}