import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");

export const config = {
  port: Number(process.env.PORT ?? 3100),
  logLevel: process.env.LOG_LEVEL ?? "info",
  backendBaseUrl: process.env.BACKEND_BASE_URL ?? "http://127.0.0.1:8000",
  internalToken: process.env.WHATSAPP_GATEWAY_INTERNAL_TOKEN ?? "",
  accountKey: process.env.WHATSAPP_ACCOUNT_KEY ?? "default",
  selfChatMode: (process.env.WHATSAPP_SELF_CHAT_MODE ?? "false") === "true",
  sessionDir: path.resolve(rootDir, process.env.WHATSAPP_SESSION_DIR ?? ".sessions"),
  browserName: process.env.WHATSAPP_BROWSER_NAME ?? "Loja Project",
  browserPlatform: process.env.WHATSAPP_BROWSER_PLATFORM ?? "Desktop",
  browserVersion: process.env.WHATSAPP_BROWSER_VERSION ?? "1.0.0",
};
