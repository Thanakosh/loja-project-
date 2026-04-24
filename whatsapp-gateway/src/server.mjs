import "dotenv/config";

import express from "express";
import pino from "pino";

import { config } from "./config.mjs";
import { WhatsAppSessionManager } from "./session-manager.mjs";

const logger = pino({
  name: "loja-whatsapp-gateway",
  level: config.logLevel,
});

const app = express();
const manager = new WhatsAppSessionManager({ config, logger });

app.use(express.json({ limit: "20mb" }));

app.get("/health", (_request, response) => {
  response.json({
    status: "ok",
    account_key: config.accountKey,
  });
});

app.use((request, response, next) => {
  if (request.path === "/health") {
    next();
    return;
  }

  if (!config.internalToken || request.header("X-Internal-Token") !== config.internalToken) {
    response.status(401).json({ detail: "Token interno invalido." });
    return;
  }

  next();
});

app.get("/session/status", (_request, response) => {
  response.json(manager.getSnapshot());
});

app.post("/session/connect", async (request, response) => {
  try {
    const snapshot = await manager.connect({
      forceRefresh: Boolean(request.body?.force_refresh),
    });
    response.json(snapshot);
  } catch (error) {
    logger.error({ err: error }, "Falha ao iniciar conexao WhatsApp");
    response.status(500).json({
      detail: error instanceof Error ? error.message : "Falha ao iniciar conexao WhatsApp",
    });
  }
});

app.post("/session/disconnect", async (_request, response) => {
  try {
    const snapshot = await manager.disconnect();
    response.json(snapshot);
  } catch (error) {
    logger.error({ err: error }, "Falha ao desconectar sessao WhatsApp");
    response.status(500).json({
      detail: error instanceof Error ? error.message : "Falha ao desconectar sessao WhatsApp",
    });
  }
});

app.post("/messages/document", async (request, response) => {
  try {
    const result = await manager.sendDocument(request.body);
    response.json(result);
  } catch (error) {
    logger.error({ err: error }, "Falha ao enviar documento WhatsApp");
    response.status(500).json({
      detail: error instanceof Error ? error.message : "Falha ao enviar documento WhatsApp",
    });
  }
});

await manager.boot();

app.listen(config.port, () => {
  logger.info({ port: config.port }, "WhatsApp gateway iniciado");
});
