"use client";
import { Suspense } from "react";
import Settings from "@medireview/views/Settings";

export default function SettingsRoute() {
  return (
    <Suspense fallback={<div className="text-center py-8 text-gray-400">로딩중...</div>}>
      <Settings />
    </Suspense>
  );
}
