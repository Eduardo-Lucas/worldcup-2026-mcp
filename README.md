# ⚽ MCP Server - Copa do Mundo 2026

Servidor MCP construído com **FastMCP** para consultar dados da Copa do Mundo FIFA 2026 diretamente de qualquer IA compatível com o protocolo MCP (Claude, Cursor, etc.).

## 🚀 Ferramentas disponíveis

| Tool | Descrição | Parâmetros |
|------|-----------|------------|
| `jogos_recentes` | Placares dos jogos mais recentes | `quantidade` (default: 5) |
| `proximos_jogos` | Próximos jogos com probabilidades | `quantidade` (default: 5) |
| `classificacao_grupo` | Tabela de um grupo específico | `grupo` (A–L) |
| `buscar_time` | Info completa de um time | `nome_time` (em inglês) |
| `todos_grupos` | Resumo de todos os 12 grupos | — |
| `estatisticas_copa` | Gols, médias e destaques | — |

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/worldcup-mcp
cd worldcup-mcp

# Instale as dependências
pip install fastmcp httpx

# Execute o servidor
python -m src.server
```

## ⚙️ Configurar no Claude Desktop

Edite `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) ou `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "copa-2026": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/caminho/absoluto/para/worldcup-mcp"
    }
  }
}
```

Reinicie o Claude Desktop. As ferramentas estarão disponíveis automaticamente.

## ⚙️ Configurar no Claude Code (VS Code)

```bash
claude mcp add copa-2026 python -- -m src.server
```

## 🧪 Rodando os testes

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## 💬 Exemplos de uso

Após conectar o servidor, você pode perguntar ao Claude:

- *"Quais foram os resultados de ontem na Copa?"*
- *"Como está o Brasil na classificação?"*
- *"Qual a probabilidade da Argentina ganhar hoje?"*
- *"Me mostra a tabela do Grupo I"*
- *"Quantos gols foram marcados na Copa até agora?"*

## 🏗️ Arquitetura

```
worldcup-mcp/
├── src/
│   └── server.py          # Servidor MCP com FastMCP
├── tests/
│   └── test_server.py     # Testes das tools
├── pyproject.toml
├── claude_desktop_config.json
└── README.md
```

## 🔌 Expandindo com SportRadar API

O servidor inclui suporte opcional à SportRadar API. Para ativar dados em tempo real:

```bash
export SPORTRADAR_API_KEY="sua_chave_aqui"
```

Os dados mockados são substituídos automaticamente quando a chave está presente.

## 📝 Conceitos MCP usados

- **`@mcp.tool()`** — expõe funções Python como ferramentas para a IA
- **Docstrings** — viram descrição automática da tool (a IA lê isso!)
- **Type hints** — definem o schema dos parâmetros
- **`mcp.run()`** — inicia o servidor via stdio

---

Construído com [FastMCP](https://github.com/jlowin/fastmcp) · Dados: SportRadar FIFA World Cup API
