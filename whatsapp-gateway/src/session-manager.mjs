import fs from "node:fs/promises";
import path from "node:path";

import makeWASocket, {
  DisconnectReason,
  fetchLatestBaileysVersion,
  useMultiFileAuthState,
} from "@whiskeysockets/baileys";
import QRCode from "qrcode";

export class WhatsAppSessionManager {
  constructor({ config, logger }) {
    this.config = config;
    this.logger = logger;
    this.socket = null;
    this.reconnectTimer = null;
    this.snapshot = {
      account_key: config.accountKey,
      status: "disconnected",
      display_name: null,
      linked_phone: null,
      self_chat_mode: config.selfChatMode,
      qr_code_data_url: null,
      qr_expires_at: null,
      last_connected_at: null,
      last_error: null,
    };
  }

  get authDir() {
    return path.join(this.config.sessionDir, this.config.accountKey);
  }

  async boot() {
    await fs.mkdir(this.authDir, { recursive: true });
    const files = await fs.readdir(this.authDir);
    if (files.length > 0) {
      await this.startSocket();
    }
  }

  getSnapshot() {
    return { ...this.snapshot };
  }

  async connect({ forceRefresh = false } = {}) {
    if (forceRefresh && this.socket) {
      await this.disconnect();
    }

    if (!this.socket) {
      await this.startSocket();
    }

    return this.getSnapshot();
  }

  async disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      try {
        await this.socket.logout();
      } catch (error) {
        this.logger.warn({ err: error }, "Falha ao encerrar sessao WhatsApp");
      }
    }

    this.socket = null;
    this.updateSnapshot({
      status: "disconnected",
      qr_code_data_url: null,
      qr_expires_at: null,
      last_error: null,
    });
    await this.notifyBackend("/api/v1/integracoes/whatsapp/webhook/session", this.getSnapshot());
    return this.getSnapshot();
  }

  async sendDocument({ to, caption, filename, content_base64, message_db_id }) {
    if (!this.socket || this.snapshot.status !== "connected") {
      throw new Error("Sessao WhatsApp nao conectada.");
    }

    const digits = String(to).replace(/\D/g, "");
    const jid = `${digits}@s.whatsapp.net`;
    const buffer = Buffer.from(content_base64, "base64");

    try {
      const result = await this.socket.sendMessage(jid, {
        document: buffer,
        mimetype: "application/pdf",
        fileName: filename,
        caption,
      });
      const gatewayMessageId = result?.key?.id ?? null;
      await this.notifyBackend("/api/v1/integracoes/whatsapp/webhook/message", {
        account_key: this.config.accountKey,
        message_db_id,
        status: "sent",
        gateway_message_id: gatewayMessageId,
        sent_at: new Date().toISOString(),
      });
      return {
        status: "sent",
        gateway_message_id: gatewayMessageId,
      };
    } catch (error) {
      await this.notifyBackend("/api/v1/integracoes/whatsapp/webhook/message", {
        account_key: this.config.accountKey,
        message_db_id,
        status: "failed",
        error_message: error instanceof Error ? error.message : "Falha ao enviar documento",
        failed_at: new Date().toISOString(),
      });
      throw error;
    }
  }

  async startSocket() {
    await fs.mkdir(this.authDir, { recursive: true });
    const { state, saveCreds } = await useMultiFileAuthState(this.authDir);
    const { version } = await fetchLatestBaileysVersion();

    this.updateSnapshot({
      status: "connecting",
      last_error: null,
    });

    const socket = makeWASocket({
      auth: state,
      version,
      printQRInTerminal: false,
      markOnlineOnConnect: false,
      syncFullHistory: false,
      browser: [
        this.config.browserName,
        this.config.browserPlatform,
        this.config.browserVersion,
      ],
    });

    socket.ev.on("creds.update", saveCreds);
    socket.ev.on("connection.update", (update) => {
      void this.handleConnectionUpdate(update);
    });

    this.socket = socket;
    return socket;
  }

  async handleConnectionUpdate(update) {
    if (update.qr) {
      const qrCodeDataUrl = await QRCode.toDataURL(update.qr);
      this.updateSnapshot({
        status: "connecting",
        qr_code_data_url: qrCodeDataUrl,
        qr_expires_at: new Date(Date.now() + 60_000).toISOString(),
        last_error: null,
      });
      await this.notifyBackend("/api/v1/integracoes/whatsapp/webhook/session", this.getSnapshot());
    }

    if (update.connection === "open") {
      const linkedPhone = this.extractLinkedPhone();
      this.updateSnapshot({
        status: "connected",
        linked_phone: linkedPhone,
        qr_code_data_url: null,
        qr_expires_at: null,
        last_connected_at: new Date().toISOString(),
        last_error: null,
      });
      await this.notifyBackend("/api/v1/integracoes/whatsapp/webhook/session", this.getSnapshot());
      return;
    }

    if (update.connection === "close") {
      const disconnectCode = update?.lastDisconnect?.error?.output?.statusCode;
      const loggedOut = disconnectCode === DisconnectReason.loggedOut;
      const errorMessage =
        update?.lastDisconnect?.error?.message ??
        (loggedOut ? "Sessao encerrada pelo WhatsApp." : "Sessao desconectada.");

      this.updateSnapshot({
        status: loggedOut ? "disconnected" : "error",
        qr_code_data_url: null,
        qr_expires_at: null,
        last_error: errorMessage,
      });
      await this.notifyBackend("/api/v1/integracoes/whatsapp/webhook/session", this.getSnapshot());

      this.socket = null;
      if (!loggedOut) {
        this.scheduleReconnect();
      }
    }
  }

  scheduleReconnect() {
    if (this.reconnectTimer) {
      return;
    }

    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      try {
        await this.startSocket();
      } catch (error) {
        this.logger.error({ err: error }, "Falha ao reconectar sessao WhatsApp");
        this.scheduleReconnect();
      }
    }, 5_000);
  }

  extractLinkedPhone() {
    const rawJid = this.socket?.user?.id;
    if (!rawJid) {
      return null;
    }
    const digits = String(rawJid).split(":")[0].replace(/\D/g, "");
    return digits ? `+${digits}` : null;
  }

  updateSnapshot(patch) {
    this.snapshot = {
      ...this.snapshot,
      ...patch,
    };
  }

  async notifyBackend(pathname, payload) {
    if (!this.config.backendBaseUrl || !this.config.internalToken) {
      return;
    }

    try {
      await fetch(`${this.config.backendBaseUrl}${pathname}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Internal-Token": this.config.internalToken,
        },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      this.logger.warn({ err: error, pathname }, "Falha ao notificar backend");
    }
  }
}
