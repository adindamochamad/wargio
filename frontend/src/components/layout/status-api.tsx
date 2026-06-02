"use client";

import { useEffect, useState } from "react";
import { cekKesehatanApi } from "@/lib/api";

export function StatusApi() {
  const [status, setStatus] = useState<"memuat" | "hidup" | "mati">("memuat");

  useEffect(() => {
    let dibatalkan = false;
    void cekKesehatanApi().then((hidup) => {
      if (!dibatalkan) {
        setStatus(hidup ? "hidup" : "mati");
      }
    });
    return () => {
      dibatalkan = true;
    };
  }, []);

  if (status === "memuat" || status === "hidup") {
    return null;
  }

  return (
    <div
      role="alert"
      className="border-b border-red-200 bg-red-50 px-4 py-2 text-center text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-100"
    >
      API tidak terjangkau. Jalankan backend:{" "}
      <code className="rounded bg-red-100 px-1 dark:bg-red-900">
        uvicorn app.main:aplikasi --reload --port 8000
      </code>
    </div>
  );
}
