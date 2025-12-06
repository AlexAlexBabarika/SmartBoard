/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{svelte,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Potted Elegance Dark Theme Tokens
        'pe-bg': '#0b0b0c',
        'pe-panel': '#121213',
        'pe-card': '#171718',
        'pe-card-hover': '#1c1c1d',
        'pe-muted': '#8f969b',
        'pe-accent': '#19c37a',
        'pe-accent-hover': '#15a366',
        'pe-chip-border': 'rgba(255,255,255,0.06)',
        'pe-chip-bg': 'rgba(255,255,255,0.04)',
        'pe-text': '#e5e7eb',
        'pe-text-dim': '#6b7280',
        'pe-border': 'rgba(255,255,255,0.08)',
        'pe-featured': '#19c37a',
      },
      boxShadow: {
        'pe-small': '0 6px 14px rgba(0,0,0,0.45)',
        'pe-medium': '0 10px 30px rgba(0,0,0,0.6)',
        'pe-card': '0 4px 16px rgba(0,0,0,0.35)',
        'pe-card-hover': '0 12px 32px rgba(0,0,0,0.5)',
        'pe-glow': '0 0 30px rgba(25,195,122,0.15)',
      },
      borderRadius: {
        'pe': '12px',
        'pe-lg': '16px',
        'pe-xl': '18px',
      },
      fontFamily: {
        'display': ['Sora', 'system-ui', 'sans-serif'],
        'body': ['DM Sans', 'system-ui', 'sans-serif'],
      },
      backdropBlur: {
        'nav': '12px',
      },
      transitionDuration: {
        '180': '180ms',
        '220': '220ms',
      },
      transitionTimingFunction: {
        'pe': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      animation: {
        'lift': 'lift 0.22s cubic-bezier(0.4, 0, 0.2, 1)',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        lift: {
          '0%': { transform: 'translateY(0)' },
          '100%': { transform: 'translateY(-6px)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        'potted-elegance': {
          'primary': '#19c37a',
          'primary-focus': '#15a366',
          'primary-content': '#ffffff',
          'secondary': '#2d2d2e',
          'secondary-focus': '#3d3d3e',
          'secondary-content': '#e5e7eb',
          'accent': '#19c37a',
          'accent-focus': '#15a366',
          'accent-content': '#ffffff',
          'neutral': '#171718',
          'neutral-focus': '#1c1c1d',
          'neutral-content': '#e5e7eb',
          'base-100': '#171718',
          'base-200': '#121213',
          'base-300': '#0b0b0c',
          'base-content': '#e5e7eb',
          'info': '#3abff8',
          'success': '#19c37a',
          'warning': '#fbbd23',
          'error': '#f87272',
        },
      },
    ],
  },
}
