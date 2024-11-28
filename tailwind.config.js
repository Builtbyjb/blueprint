/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./main/static/main/scripts/*.js", "./main/templates/main/*.html"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          100: '#1E293B',
          200: '#0F172A',
        }
      }
    },
  },
  plugins: [],
}

