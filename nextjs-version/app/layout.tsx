import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'RevOps Agent - Next.js' };

const theme = createTheme({ palette: { mode: 'light' } });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider theme={theme}><CssBaseline />{children}</ThemeProvider>
      </body>
    </html>
  );
}
