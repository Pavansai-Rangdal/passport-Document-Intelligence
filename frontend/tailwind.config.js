/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: '#1e2d3d',
          dark: '#172435',
          light: '#253b50',
          hover: '#2e4a63',
          active: '#3a5f7d',
          border: '#2a3f54',
          text: '#94b4cc',
          'text-muted': '#5a7a93',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [],
}
