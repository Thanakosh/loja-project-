"""
Módulo LLM — Desativado nesta versão.

Integração com Ollama (modelos locais) e Open Interpreter foi removida.
Análise de notas fiscais via LLM está planejada para uma versão futura,
quando será reimplementada com uma arquitetura mais robusta (fila assíncrona
com persistência de estado).
"""

from fastapi import APIRouter

router = APIRouter(tags=["LLM"])

# Nenhum endpoint ativo nesta versão.
# Os endpoints de /ollama, /open-interpreter e /analisar-nota-fiscal
# serão reintroduzidos em versão futura.
