/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './content/**/*.json',
    './index.html',
  ],
  darkMode: 'media',
  theme: {
    extend: {
      // fontFamily: {
      //   sans: ['Inter', 'system-ui', 'sans-serif'],
      //   heading: ['Manrope', 'system-ui', 'sans-serif'],
      //   mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      // },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
}