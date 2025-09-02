/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
      './templates/**/*.html',
      './*/templates/**/*.html',
      './node_modules/flowbite/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4361ee',
        secondary: '#3f37c9',
        accent: '#4895ef',
        success: '#4cc9f0',
        warning: '#f8961e',
        danger: '#f72585',
        info: '#560bad',
      },
    },
  },
  plugins: [require('flowbite/plugin')],
}
