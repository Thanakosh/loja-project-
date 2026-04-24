# WhatsApp Gateway

Gateway estilo OpenClaw para sessao WhatsApp Web via Baileys.

Objetivo:

- manter a sessao vinculada por QR em um processo separado
- expor contrato HTTP interno para backend FastAPI
- enviar documentos PDF de orcamentos

## Endpoints internos

- `GET /health`
- `GET /session/status`
- `POST /session/connect`
- `POST /session/disconnect`
- `POST /messages/document`

Todos, exceto `GET /health`, exigem `X-Internal-Token`.

## Configuracao

Crie um `.env` neste diretorio a partir de `.env.example`.

Variaveis principais:

- `PORT`: porta HTTP do gateway. Padrao: `3100`.
- `BACKEND_BASE_URL`: URL base do backend FastAPI. Exemplo: `http://127.0.0.1:8000`.
- `WHATSAPP_GATEWAY_INTERNAL_TOKEN`: token compartilhado com o backend.
- `WHATSAPP_ACCOUNT_KEY`: identificador logico da conta. Padrao: `default`.
- `WHATSAPP_SESSION_DIR`: diretorio local da sessao. Padrao: `.sessions`.

No backend, configure as mesmas credenciais:

```env
WHATSAPP_GATEWAY_URL=http://127.0.0.1:3100
WHATSAPP_GATEWAY_INTERNAL_TOKEN=mesmo-token-do-gateway
WHATSAPP_ACCOUNT_KEY=default
WHATSAPP_DEFAULT_COUNTRY=55
```

`WHATSAPP_GATEWAY_INTERNAL_TOKEN` deve ser um segredo real em ambiente de uso.
Nao use valor vazio fora de desenvolvimento controlado.

## Execucao local

Instale as dependencias:

```bash
npm install
```

Inicie o gateway:

```bash
npm run dev
```

Para uso sem watch:

```bash
npm start
```

Confirme se o gateway respondeu:

```bash
curl http://127.0.0.1:3100/health
```

## Teste operacional

1. Suba o backend com a migration aplicada.
2. Suba este gateway.
3. Acesse a tela de Configuracoes da Loja.
4. Clique em Conectar no card Canal WhatsApp.
5. Escaneie o QR com um numero dedicado, preferencialmente WhatsApp Business.
6. Crie ou abra um orcamento com cliente que tenha telefone valido.
7. Clique em WhatsApp na tela de Orcamentos.
8. Confirme se a mensagem foi enviada e se a tabela `whatsapp_message` registrou o status.

## Fluxo

1. Backend chama `POST /session/connect`
2. Gateway inicia o socket Baileys e retorna QR em `qr_code_data_url`
3. Apos o scan, o gateway notifica o backend em:
   - `POST /api/v1/integracoes/whatsapp/webhook/session`
   - `POST /api/v1/integracoes/whatsapp/webhook/message`

## Observacoes

- O diretorio `.sessions/` deve permanecer fora do git.
- O numero ideal e dedicado para operacao comercial.
- O processo do gateway precisa ficar ativo para envio e reconexao.
- Para refazer pareamento do zero, encerre o gateway, remova a sessao local correspondente em `.sessions/` e conecte novamente.
- O backend respeita opt-out ativo do cliente antes de enviar orcamentos.
