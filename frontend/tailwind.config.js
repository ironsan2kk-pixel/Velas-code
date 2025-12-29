/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Dark theme (default)
        dark: {
          'bg-primary': '#0d1117',
          'bg-secondary': '#161b22',
          'bg-tertiary': '#21262d',
          'bg-card': '#161b22',
          'border': '#30363d',
          'border-light': '#3d444d',
          'text-primary': '#f0f6fc',
          'text-secondary': '#8b949e',
          'text-muted': '#6e7681',
        },
        // Light theme
        light: {
          'bg-primary': '#ffffff',
          'bg-secondary': '#f6f8fa',
          'bg-tertiary': '#eaeef2',
          'bg-card': '#ffffff',
          'border': '#d0d7de',
          'border-light': '#e0e4e8',
          'text-primary': '#1f2328',
          'text-secondary': '#656d76',
          'text-muted': '#8c959f',
        },
        // Accent colors (same for both themes)
        accent: {
          'green': '#238636',
          'green-light': '#2ea043',
          'green-dark': '#1a7f37',
          'red': '#da3633',
          'red-light': '#f85149',
          'red-dark': '#cf222e',
          'blue': '#1f6feb',
          'blue-light': '#388bfd',
          'blue-dark': '#0969da',
          'yellow': '#d29922',
          'yellow-light': '#e3b341',
          'yellow-dark': '#9a6700',
          'purple': '#8957e5',
          'purple-light': '#a371f7',
          'purple-dark': '#8250df',
        },
        // Trading specific
        long: '#238636',
        short: '#da3633',
        profit: '#238636',
        loss: '#da3633',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'Monaco', 'monospace'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      borderRadius: {
        'sm': '0.25rem',
        'md': '0.5rem',
        'lg': '0.75rem',
        'xl': '1rem',
        '2xl': '1.5rem',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
        'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
        'glow-green': '0 0 20px rgba(35, 134, 54, 0.3)',
        'glow-red': '0 0 20px rgba(218, 54, 51, 0.3)',
        'glow-blue': '0 0 20px rgba(31, 111, 235, 0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
      transitionDuration: {
        '250': '250ms',
        '350': '350ms',
      },
      screens: {
        'xs': '475px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
      },
      minHeight: {
        'screen-minus-header': 'calc(100vh - 64px)',
      },
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
    },
  },
  plugins: [],
}
