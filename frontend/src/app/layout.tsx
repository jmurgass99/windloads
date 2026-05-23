import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'WindLoadJm',
  description: 'Wind loads — EC1, ASCE 7, NSR-10',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  )
}
