import './globals.css'
import Link from 'next/link'

export const metadata = {
  title: 'Activity App',
  description: 'Frontend for Activity App',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <nav style={{ padding: '20px', backgroundColor: '#f0f0f0', marginBottom: '20px' }}>
          <Link href="/" style={{ marginRight: '15px' }}>Home</Link>
          <Link href="/register" style={{ marginRight: '15px' }}>Register</Link>
          <Link href="/login" style={{ marginRight: '15px' }}>Login</Link>
          <Link href="/dashboard" style={{ marginRight: '15px' }}>Dashboard</Link>
        </nav>
        <main style={{ padding: '0 20px' }}>
          {children}
        </main>
      </body>
    </html>
  )
}
