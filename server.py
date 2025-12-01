#!/usr/bin/env python3
"""
Servidor MCP - Sistema de Aprendizado Legislação de Trânsito
Com rastreamento de progresso, simulados e evolução do usuário
VERSÃO COMPLETA
"""
import os
import json
import sys
import sqlite3
import random
import logging
import requests
import time
from datetime import datetime

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_filename = os.path.join(LOG_DIR, f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)
logger.info("=" * 50)
logger.info("Servidor MCP iniciado")
logger.info(f"Log salvo em: {log_filename}")
logger.info("=" * 50)

DATABASE_PATH = "C:/Users/jc130/OneDrive/Área de Trabalho/Agente Legislacao/agente_transito/database.db"

# ============================================
# CONEXÃO COM BANCO DE DADOS
# ============================================

def conectar_db():
    """Conecta ao banco SQLite."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        return None
    
#==============================================
# FUNÇÃO DE CONSULTA AO MODELO FINE-TUNING
#==============================================

# def query_api(
#     api_url: str,
#     prompt: str,
#     max_tokens: int = 256,
#     temperature: float = 0.7,
#     top_p: float = 0.9,
#     timeout: int = 60,
# ) -> dict:
#     """Query the remote predict API with a one-shot prompt and return a dict.

#     Args:
#         api_url: Base URL of the API (e.g. https://xxxx-xxxx.ngrok.io).
#         prompt: The prompt string to send to the model.
#         max_tokens: Maximum tokens to request.
#         temperature: Sampling temperature.
#         top_p: Nucleus sampling p.
#         timeout: Request timeout in seconds for the predict request.

#     Returns:
#         A dictionary containing the JSON response from the server or an
#         error key with details when the request fails.
#     """
#     api_url = "https://jade-tachyauxetic-maribel.ngrok-free.dev"
#     session = requests.Session()

#     # Quick health check
#     try:
#         health = session.get(f"{api_url}/health", timeout=5)
#         if health.status_code != 200:
#             return {"error": f"API not accessible at {api_url} (status={health.status_code})"}
#     except requests.exceptions.RequestException as e:
#         return {"error": f"API access error: {e}"}

#     payload = {
#         "prompt": prompt,
#         "max_tokens": max_tokens,
#         "temperature": temperature,
#         "top_p": top_p,
#     }

#     try:
#         start = time.time()
#         resp = session.post(f"{api_url}/predict", json=payload, timeout=timeout)
#         elapsed = time.time() - start
#         resp.raise_for_status()
#         result = resp.json()
#         result["elapsed_time"] = elapsed
#         return {"resposta":result}

#     except requests.exceptions.Timeout:
#         return {"error": "Timeout - the request took too long"}
#     except requests.exceptions.ConnectionError:
#         return {"error": "Connection error when contacting the API"}
#     except Exception as e:
#         return {"error": str(e)}

# ============================================
# FUNÇÕES DE SIMULADO
# ============================================

def obter_simulado_geral() -> dict:
    """Retorna um simulado geral com 30 questões formatadas em texto"""
    try:
        conn = conectar_db()
        if not conn:
            return {"erro": "Falha ao conectar ao banco"}
        
        cursor = conn.cursor()
        simulado = {
            "tipo": "simulado_geral",
            "total_questoes": 30,
            "secoes": {}
        }
        
        # 1. Legislação de Trânsito (18 questões)
        legislacao_tipos = ['legislacao', 'infracao', 'norma_circulacao', 'sinalizacao', 'processo_habilitacao', 'veiculo']
        cursor.execute(
            f"SELECT id FROM categories WHERE name IN ({','.join(['?']*len(legislacao_tipos))})",
            legislacao_tipos
        )
        legislacao_ids = [row[0] for row in cursor.fetchall()]
        
        if legislacao_ids:
            placeholders = ','.join(['?'] * len(legislacao_ids))
            cursor.execute(
                f"SELECT id, question, alternative_a, alternative_b, alternative_c, alternative_d, correct_alternative, photo FROM questions WHERE category_id IN ({placeholders}) ORDER BY RANDOM() LIMIT 18",
                legislacao_ids
            )
            simulado["secoes"]["legislacao"] = {
                "nome": "Legislação de Trânsito",
                "total": 18,
                "questoes": [dict(row) for row in cursor.fetchall()]
            }
        
        # 2. Direção Defensiva (5 questões)
        cursor.execute("SELECT id FROM categories WHERE name = 'direcao_defensiva'")
        cat_defens = cursor.fetchone()
        if cat_defens:
            cursor.execute(
                "SELECT id, question, alternative_a, alternative_b, alternative_c, alternative_d, correct_alternative, photo FROM questions WHERE category_id = ? ORDER BY RANDOM() LIMIT 5",
                (cat_defens[0],)
            )
            simulado["secoes"]["direcao_defensiva"] = {
                "nome": "Direção Defensiva",
                "total": 5,
                "questoes": [dict(row) for row in cursor.fetchall()]
            }
        
        # 3. Primeiros Socorros (3 questões)
        cursor.execute("SELECT id FROM categories WHERE name = 'primeiros_socorros'")
        cat_socorros = cursor.fetchone()
        if cat_socorros:
            cursor.execute(
                "SELECT id, question, alternative_a, alternative_b, alternative_c, alternative_d, correct_alternative, photo FROM questions WHERE category_id = ? ORDER BY RANDOM() LIMIT 3",
                (cat_socorros[0],)
            )
            simulado["secoes"]["primeiros_socorros"] = {
                "nome": "Primeiros Socorros",
                "total": 3,
                "questoes": [dict(row) for row in cursor.fetchall()]
            }
        
        # 4. Cidadania e Meio Ambiente (2 questões)
        cursor.execute("SELECT id FROM categories WHERE name = 'meio_ambiente'")
        cat_cidadania = cursor.fetchone()
        if cat_cidadania:
            cursor.execute(
                "SELECT id, question, alternative_a, alternative_b, alternative_c, alternative_d, correct_alternative, photo FROM questions WHERE category_id = ? ORDER BY RANDOM() LIMIT 2",
                (cat_cidadania[0],)
            )
            simulado["secoes"]["cidadania"] = {
                "nome": "Cidadania e Meio Ambiente",
                "total": 2,
                "questoes": [dict(row) for row in cursor.fetchall()]
            }
        
        # 5. Mecânica Básica (2 questões)
        cursor.execute("SELECT id FROM categories WHERE name = 'mecanica'")
        cat_mecanica = cursor.fetchone()
        if cat_mecanica:
            cursor.execute(
                "SELECT id, question, alternative_a, alternative_b, alternative_c, alternative_d, correct_alternative, photo FROM questions WHERE category_id = ? ORDER BY RANDOM() LIMIT 2",
                (cat_mecanica[0],)
            )
            simulado["secoes"]["mecanica"] = {
                "nome": "Mecânica Básica",
                "total": 2,
                "questoes": [dict(row) for row in cursor.fetchall()]
            }
        
        conn.close()
        
        return {
            "sucesso": True,
            "simulado_json": simulado,
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter simulado geral: {e}")
        return {"erro": str(e)}

def obter_simulado_categoria(category_name: str) -> dict:
    """Retorna 10 questões aleatórias de uma categoria formatadas em texto"""
    try:
        conn = conectar_db()
        if not conn:
            return {"erro": "Falha ao conectar ao banco"}
        
        cursor = conn.cursor()
        if category_name == "legislacao":
            categorias_legislacao = ['infracao', 'norma_circulacao', 'sinalizacao', 'processo_habilitacao', 'veiculo']
            cursor.execute(
                f"SELECT id FROM categories WHERE name IN ({','.join(['?']*len(categorias_legislacao))})",
                categorias_legislacao
            )
            legislacao_ids = [row[0] for row in cursor.fetchall()]
            if legislacao_ids:
                placeholders = ','.join(['?'] * len(legislacao_ids))
                cursor.execute(
                    f"SELECT id, number, question, alternative_a, alternative_b, alternative_c, alternative_d, correct_alternative, photo FROM questions WHERE category_id IN ({placeholders}) ORDER BY RANDOM() LIMIT 10",
                    legislacao_ids
                )
                questoes = [dict(row) for row in cursor.fetchall()]
            else:
                questoes = []
        else:
            cursor.execute("SELECT id, name, description FROM categories WHERE name = ?", (category_name,))
            categoria = cursor.fetchone()
            
            if not categoria:
                return {"erro": f"Categoria '{category_name}' não encontrada"}
            
            cat_id = categoria[0]
            
            cursor.execute(
                "SELECT id, number, question, alternative_a, alternative_b, alternative_c, alternative_d, correct_alternative, photo FROM questions WHERE category_id = ? ORDER BY RANDOM() LIMIT 10",
                (cat_id,)
            )
            questoes = [dict(row) for row in cursor.fetchall()]
            conn.close()
        
        return {
            "sucesso": True,
            "categoria": category_name,
            "total_questoes": len(questoes),
            "simulado_json": questoes
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter simulado categoria: {e}")
        return {"erro": str(e)}

def registrar_respostas_simulado(user_id: int, respostas: dict) -> dict:
    """Registra respostas e retorna estatísticas formatadas"""
    try:
        conn = conectar_db()
        if not conn:
            return {"erro": "Falha ao conectar ao banco"}
        
        cursor = conn.cursor()
        
        estatisticas = {
            "user_id": user_id,
            "total_questoes": len(respostas),
            "total_corretas": 0,
            "total_erradas": 0,
            "percentual_acerto": 0,
            "por_categoria": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for question_id, resposta_usuario in respostas.items():
            try:
                question_id = int(question_id)
                
                cursor.execute(
                    "SELECT category_id, correct_alternative FROM questions WHERE id = ?",
                    (question_id,)
                )
                resultado = cursor.fetchone()
                
                if not resultado:
                    continue
                
                category_id, resposta_correta = resultado
                is_correct = resposta_usuario.upper() == resposta_correta
                
                cursor.execute(
                    """INSERT INTO user_answers (user_id, question_id, category_id, user_answer, correct_answer, is_correct)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, question_id, category_id, resposta_usuario.upper(), resposta_correta, is_correct)
                )
                
                cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
                cat_name = cursor.fetchone()[0]
                
                if cat_name not in estatisticas["por_categoria"]:
                    estatisticas["por_categoria"][cat_name] = {
                        "total": 0,
                        "corretas": 0,
                        "erradas": 0,
                        "percentual": 0
                    }
                
                estatisticas["por_categoria"][cat_name]["total"] += 1
                
                if is_correct:
                    estatisticas["total_corretas"] += 1
                    estatisticas["por_categoria"][cat_name]["corretas"] += 1
                else:
                    estatisticas["total_erradas"] += 1
                    estatisticas["por_categoria"][cat_name]["erradas"] += 1
                
                cursor.execute(
                    "SELECT id, total_answered, total_correct FROM user_progress WHERE user_id = ? AND category_id = ?",
                    (user_id, category_id)
                )
                progress = cursor.fetchone()
                
                if progress:
                    progress_id, total_answered, total_correct = progress
                    new_total = total_answered + 1
                    new_correct = total_correct + (1 if is_correct else 0)
                    percentage = (new_correct / new_total) * 100
                    
                    cursor.execute(
                        """UPDATE user_progress 
                           SET total_answered = ?, total_correct = ?, percentage = ?, last_updated = CURRENT_TIMESTAMP
                           WHERE id = ?""",
                        (new_total, new_correct, percentage, progress_id)
                    )
                else:
                    new_total = 1
                    new_correct = 1 if is_correct else 0
                    percentage = (new_correct / new_total) * 100
                    
                    cursor.execute(
                        """INSERT INTO user_progress (user_id, category_id, total_answered, total_correct, percentage)
                           VALUES (?, ?, ?, ?, ?)""",
                        (user_id, category_id, new_total, new_correct, percentage)
                    )
            
            except Exception as e:
                logger.error(f"Erro ao registrar resposta {question_id}: {e}")
                continue
        
        if estatisticas["total_questoes"] > 0:
            estatisticas["percentual_acerto"] = round((estatisticas["total_corretas"] / estatisticas["total_questoes"]) * 100, 2)
        
        for categoria in estatisticas["por_categoria"]:
            cat_data = estatisticas["por_categoria"][categoria]
            if cat_data["total"] > 0:
                cat_data["percentual"] = round((cat_data["corretas"] / cat_data["total"]) * 100, 2)
        
        conn.commit()
        conn.close()
        
        return {
            "sucesso": True,
            "estatisticas": estatisticas
        }
    
    except Exception as e:
        logger.error(f"Erro ao registrar respostas: {e}")
        return {"erro": str(e)}

def obter_progresso_usuario(user_id: int) -> dict:
    """Retorna progresso formatado"""
    try:
        conn = conectar_db()
        if not conn:
            return {"erro": "Falha ao conectar ao banco"}
        
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT c.name, up.total_answered, up.total_correct, up.percentage
               FROM user_progress up
               JOIN categories c ON up.category_id = c.id
               WHERE up.user_id = ?
               ORDER BY up.percentage DESC""",
            (user_id,)
        )
        
        resultados = cursor.fetchall()
        conn.close()
        
        texto_progresso = "\n" + "=" * 60 + "\n"
        texto_progresso += "📊 SEU PROGRESSO GERAL\n"
        texto_progresso += "=" * 60 + "\n\n"
        
        if not resultados:
            texto_progresso += "Você ainda não respondeu nenhuma questão.\n"
        else:
            for row in resultados:
                nome, respondidas, corretas, percentual = row
                texto_progresso += f"📚 {nome}\n"
                texto_progresso += f"   Respondidas: {respondidas} | Corretas: {corretas} | Acerto: {percentual:.1f}%\n\n"
        
        texto_progresso += "=" * 60 + "\n"
        
        progresso = {
            "user_id": user_id,
            "categorias": [
                {
                    "nome": row[0],
                    "total_respondidas": row[1],
                    "total_corretas": row[2],
                    "percentual_acerto": round(row[3], 2) if row[3] else 0
                }
                for row in resultados
            ]
        }
        
        return {"sucesso": True, "texto": texto_progresso, "progresso": progresso}
    
    except Exception as e:
        logger.error(f"Erro ao obter progresso: {e}")
        return {"erro": str(e)}

# ============================================
# FUNÇÕES DE EVOLUÇÃO DE SIMULADOS
# ============================================

def registrar_simulado_categoria(user_id: int, categoria_name: str, respostas: dict, tempo_segundos: int = None) -> dict:
    """
    Registra um simulado de categoria específica e salva para acompanhamento da evolução.
    """
    try:
        conn = conectar_db()
        if not conn:
            return {"erro": "Falha ao conectar ao banco"}
        
        cursor = conn.cursor()
        
        estatisticas = {
            "user_id": user_id,
            "categoria": categoria_name,
            "total_questoes": len(respostas),
            "total_corretas": 0,
            "total_erradas": 0,
            "percentual_acerto": 0,
            "data_realizacao": datetime.now().isoformat()
        }
        
        # Verificar categoria
        if categoria_name == "legislacao":
            categorias_legislacao = ['infracao', 'norma_circulacao', 'sinalizacao', 
                                     'processo_habilitacao', 'veiculo']
            cursor.execute(
                f"SELECT id FROM categories WHERE name IN ({','.join(['?']*len(categorias_legislacao))})",
                categorias_legislacao
            )
            category_ids = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute("SELECT id FROM categories WHERE name = ?", (categoria_name,))
            cat_row = cursor.fetchone()
            if not cat_row:
                return {"erro": f"Categoria '{categoria_name}' não encontrada"}
            category_ids = [cat_row[0]]
        
        # Processar cada resposta
        for question_id, resposta_usuario in respostas.items():
            try:
                question_id = int(question_id)
                
                cursor.execute(
                    "SELECT category_id, correct_alternative FROM questions WHERE id = ?",
                    (question_id,)
                )
                resultado = cursor.fetchone()
                
                if not resultado:
                    logger.warning(f"Questão {question_id} não encontrada")
                    continue
                
                category_id, resposta_correta = resultado
                is_correct = resposta_usuario.upper() == resposta_correta
                
                if is_correct:
                    estatisticas["total_corretas"] += 1
                else:
                    estatisticas["total_erradas"] += 1
                
                cursor.execute(
                    """INSERT INTO user_answers (user_id, question_id, category_id, user_answer, correct_answer, is_correct)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, question_id, category_id, resposta_usuario.upper(), resposta_correta, is_correct)
                )
                
            except Exception as e:
                logger.error(f"Erro ao processar questão {question_id}: {e}")
                continue
        
        if estatisticas["total_questoes"] > 0:
            estatisticas["percentual_acerto"] = round(
                (estatisticas["total_corretas"] / estatisticas["total_questoes"]) * 100, 2
            )
        
        # Inserir registro do simulado
        cursor.execute(
            """INSERT INTO simulados_realizados 
               (user_id, categoria_name, total_questoes, total_corretas, total_erradas, 
                percentual_acerto, tempo_realizacao)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, categoria_name, estatisticas["total_questoes"], 
             estatisticas["total_corretas"], estatisticas["total_erradas"],
             estatisticas["percentual_acerto"], tempo_segundos)
        )
        
        simulado_id = cursor.lastrowid
        
        # Atualizar progresso geral do usuário
        for cat_id in category_ids:
            cursor.execute(
                """SELECT id, total_answered, total_correct 
                   FROM user_progress 
                   WHERE user_id = ? AND category_id = ?""",
                (user_id, cat_id)
            )
            progress = cursor.fetchone()
            
            cursor.execute(
                """SELECT COUNT(*), SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
                   FROM user_answers 
                   WHERE user_id = ? AND category_id = ? AND question_id IN ({})""".format(
                       ','.join(['?'] * len(respostas))
                   ),
                (user_id, cat_id, *[int(qid) for qid in respostas.keys()])
            )
            count_result = cursor.fetchone()
            questoes_da_categoria = count_result[0] if count_result[0] else 0
            corretas_da_categoria = count_result[1] if count_result[1] else 0
            
            if progress and questoes_da_categoria > 0:
                progress_id, total_answered, total_correct = progress
                new_total = total_answered + questoes_da_categoria
                new_correct = total_correct + corretas_da_categoria
                percentage = (new_correct / new_total) * 100 if new_total > 0 else 0
                
                cursor.execute(
                    """UPDATE user_progress 
                       SET total_answered = ?, total_correct = ?, percentage = ?, 
                           last_updated = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (new_total, new_correct, percentage, progress_id)
                )
            elif questoes_da_categoria > 0:
                percentage = (corretas_da_categoria / questoes_da_categoria) * 100
                cursor.execute(
                    """INSERT INTO user_progress 
                       (user_id, category_id, total_answered, total_correct, percentage)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, cat_id, questoes_da_categoria, corretas_da_categoria, percentage)
                )
        
        conn.commit()
        conn.close()
        
        return {
            "sucesso": True,
            "simulado_id": simulado_id,
            "estatisticas": estatisticas
        }
    
    except Exception as e:
        logger.error(f"Erro ao registrar simulado: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return {"erro": str(e)}

def obter_evolucao_usuario(user_id: int, categoria_name: str = None, limite: int = 10) -> dict:
    """
    Retorna a evolução do usuário ao longo dos simulados realizados.
    """
    try:
        conn = conectar_db()
        if not conn:
            return {"erro": "Falha ao conectar ao banco"}
        
        cursor = conn.cursor()
        
        if categoria_name:
            cursor.execute(
                """SELECT id, categoria_name, total_questoes, total_corretas, 
                          total_erradas, percentual_acerto, tempo_realizacao, 
                          data_realizacao
                   FROM simulados_realizados
                   WHERE user_id = ? AND categoria_name = ?
                   ORDER BY data_realizacao DESC
                   LIMIT ?""",
                (user_id, categoria_name, limite)
            )
        else:
            cursor.execute(
                """SELECT id, categoria_name, total_questoes, total_corretas, 
                          total_erradas, percentual_acerto, tempo_realizacao, 
                          data_realizacao
                   FROM simulados_realizados
                   WHERE user_id = ?
                   ORDER BY data_realizacao DESC
                   LIMIT ?""",
                (user_id, limite)
            )
        
        simulados = []
        percentuais = []
        
        for row in cursor.fetchall():
            simulado_data = {
                "id": row[0],
                "categoria": row[1],
                "total_questoes": row[2],
                "corretas": row[3],
                "erradas": row[4],
                "percentual": row[5],
                "tempo_segundos": row[6],
                "data": row[7]
            }
            simulados.append(simulado_data)
            percentuais.append(row[5])
        
        # Inverter para ordem cronológica
        simulados_cronologico = list(reversed(simulados))
        percentuais_cronologico = list(reversed(percentuais))
        
        # Análise de evolução
        analise = {
            "total_simulados": len(simulados),
            "media_percentual": round(sum(percentuais) / len(percentuais), 2) if percentuais else 0,
            "melhor_resultado": max(percentuais) if percentuais else 0,
            "pior_resultado": min(percentuais) if percentuais else 0,
            "ultimo_resultado": percentuais[0] if percentuais else 0
        }
        
        # Tendência de evolução
        if len(percentuais_cronologico) >= 4:
            meio = len(percentuais_cronologico) // 2
            media_primeira_metade = sum(percentuais_cronologico[:meio]) / meio
            media_segunda_metade = sum(percentuais_cronologico[meio:]) / (len(percentuais_cronologico) - meio)
            diferenca = media_segunda_metade - media_primeira_metade
            
            if diferenca > 5:
                analise["tendencia"] = "Melhorando! 📈"
            elif diferenca < -5:
                analise["tendencia"] = "Em declínio 📉"
            else:
                analise["tendencia"] = "Estável ➡️"
            
            analise["diferenca_percentual"] = round(diferenca, 2)
        else:
            analise["tendencia"] = "Dados insuficientes para análise"
            analise["diferenca_percentual"] = 0
        
        conn.close()
        
        return {
            "sucesso": True,
            "user_id": user_id,
            "categoria": categoria_name if categoria_name else "Todas",
            "simulados": simulados,
            "analise": analise
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter evolução: {e}")
        return {"erro": str(e)}

# ============================================
# FERRAMENTAS MCP
# ============================================

TOOLS = [
    {
        "name": "simulado_geral",
        "description": "Retorna um simulado geral com 30 questões formatadas",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "ID do usuário"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "simulado_categoria",
        "description": "Retorna 10 questões de uma categoria específica",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category_name": {"type": "string", "description": "Nome da categoria"}
            },
            "required": ["category_name"]
        }
    },
    {
        "name": "registrar_respostas",
        "description": "Registra respostas de simulado genérico e retorna estatísticas",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "ID do usuário"},
                "respostas": {"type": "object", "description": "question_id: resposta"}
            },
            "required": ["user_id", "respostas"]
        }
    },
    {
        "name": "registrar_simulado_categoria",
        "description": "Registra simulado de categoria e salva para evolução",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "ID do usuário"},
                "categoria_name": {"type": "string", "description": "Nome da categoria"},
                "respostas": {"type": "object", "description": "question_id: resposta"},
                "tempo_segundos": {"type": "integer", "description": "Tempo em segundos (opcional)"}
            },
            "required": ["user_id", "categoria_name", "respostas"]
        }
    },
    {
        "name": "obter_progresso",
        "description": "Retorna progresso geral do usuário",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "ID do usuário"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "obter_evolucao",
        "description": "Retorna evolução do usuário nos simulados com análise",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "ID do usuário"},
                "categoria_name": {"type": "string", "description": "Filtrar por categoria (opcional)"},
                "limite": {"type": "integer", "description": "Número máximo de simulados (padrão: 10)"}
            },
            "required": ["user_id"]
        }
    }
]

# ============================================
# PROTOCOLO JSON-RPC
# ============================================

def processar_mensagem(msg: dict) -> dict:
    """Processa mensagem JSON-RPC"""
    try:
        method = msg.get("method", "")
        msg_id = msg.get("id", 1)
        
        logger.debug(f"Recebido: {method}")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "mcp-simulado-transito",
                        "version": "3.0"
                    }
                }
            }
        
        elif method == "tools/list" or method == "list_tools":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS}
            }
        
        elif method == "tools/call" or method == "call_tool":
            nome = msg.get("params", {}).get("name", "")
            args = msg.get("params", {}).get("arguments", {})
            
            if nome == "simulado_geral":
                resultado = obter_simulado_geral()
            elif nome == "simulado_categoria":
                resultado = obter_simulado_categoria(args.get("category_name"))
            elif nome == "registrar_respostas":
                resultado = registrar_respostas_simulado(args.get("user_id"), args.get("respostas", {}))
            elif nome == "registrar_simulado_categoria":
                resultado = registrar_simulado_categoria(
                    args.get("user_id"), 
                    args.get("categoria_name"),
                    args.get("respostas", {}),
                    args.get("tempo_segundos")
                )
            elif nome == "obter_progresso":
                resultado = obter_progresso_usuario(args.get("user_id"))
            elif nome == "obter_evolucao":
                resultado = obter_evolucao_usuario(
                    args.get("user_id"),
                    args.get("categoria_name"),
                    args.get("limite", 10)
                )
            else:
                resultado = {"erro": f"Ferramenta '{nome}' não encontrada"}
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(resultado, ensure_ascii=False)}]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Método '{method}' não encontrado"}
            }
    
    except Exception as e:
        logger.error(f"Erro: {e}")
        return {
            "jsonrpc": "2.0",
            "id": msg.get("id", 1),
            "error": {"code": -32603, "message": str(e)}
        }

# ============================================
# LOOP PRINCIPAL
# ============================================

def main():
    while True:
        try:
            linha = sys.stdin.readline()
            if not linha:
                break
            
            msg = json.loads(linha.strip())
            method = msg.get("method", "")
            
            if method and method.startswith("notifications/"):
                logger.debug(f"Notificação: {method}")
                continue
            
            resposta = processar_mensagem(msg)
            logger.debug(f"Enviando: {method}")
            sys.stdout.write(json.dumps(resposta) + "\n")
            sys.stdout.flush()
        
        except json.JSONDecodeError as e:
            logger.error(f"Erro JSON: {e}")
        except Exception as e:
            logger.error(f"Erro: {e}")

if __name__ == "__main__":
    main()