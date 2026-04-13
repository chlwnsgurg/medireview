import "@/styles/globals.css";

export const metadata = {
  title: {
    default: "MediReview — AI 리뷰 답글 관리",
    template: "%s | MediReview",
  },
  description: "병·의원 통합 리뷰 관리 및 AI 자동 답글 도구",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="preload"
          href="/fonts/PretendardVariable.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
      </head>
      <body className="min-h-[100dvh] bg-[var(--color-bg)] text-[var(--color-text)]">
        {children}
      </body>
    </html>
  );
}
