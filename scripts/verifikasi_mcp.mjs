#!/usr/bin/env node
/**
 * Verifikasi MongoDB MCP Server — tool find stok rendah.
 * Butuh MONGODB_URI di environment (.env di-load via dotenv-cli atau export manual).
 */
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const __dir = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dir, "..");

function muatEnv() {
  try {
    const envPath = resolve(root, ".env");
    const isi = readFileSync(envPath, "utf8");
    for (const baris of isi.split("\n")) {
      const t = baris.trim();
      if (!t || t.startsWith("#")) continue;
      const i = t.indexOf("=");
      if (i === -1) continue;
      const k = t.slice(0, i);
      const v = t.slice(i + 1);
      if (!process.env[k]) process.env[k] = v;
    }
  } catch {
    /* .env opsional jika sudah di-export */
  }
}

async function main() {
  muatEnv();
  const uri = process.env.MONGODB_URI;
  if (!uri || uri.includes("PASSWORD")) {
    console.error("GAGAL: MONGODB_URI belum valid");
    process.exit(1);
  }

  const transport = new StdioClientTransport({
    command: "npx",
    args: ["-y", "mongodb-mcp-server@latest"],
    env: {
      ...process.env,
      MDB_MCP_CONNECTION_STRING: uri,
    },
  });

  const klien = new Client({ name: "wargio-verifikasi", version: "1.0.0" });
  await klien.connect(transport);

  const daftar = await klien.listTools();
  const namaTools = daftar.tools.map((t) => t.name);
  if (!namaTools.includes("find")) {
    console.error("GAGAL: tool find tidak ditemukan. Tools:", namaTools.join(", "));
    process.exit(1);
  }
  console.log("OK: MCP tools —", namaTools.slice(0, 8).join(", "), "...");

  const hasil = await klien.callTool({
    name: "find",
    arguments: {
      database: process.env.MONGODB_DATABASE || "wargio_demo",
      collection: "products",
      filter: { $expr: { $lte: ["$stock_current", "$stock_minimum"] } },
      limit: 5,
    },
  });

  const teks = hasil.content?.[0]?.text || JSON.stringify(hasil);
  if (teks.includes("error") && !teks.includes("stock")) {
    console.error("GAGAL: find MCP —", teks.slice(0, 300));
    process.exit(1);
  }

  console.log("OK: MCP find stok rendah berhasil");
  console.log(teks.slice(0, 400));
  await klien.close();
  process.exit(0);
}

main().catch((e) => {
  console.error("GAGAL:", e.message);
  process.exit(1);
});
