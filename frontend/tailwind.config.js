module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            pre: {
              padding: '1em',
              background: 'rgb(45, 45, 45)',
              code: {
                background: 'transparent',
                padding: '0',
              },
            },
            code: {
              background: 'rgb(45, 45, 45)',
              padding: '0.25em 0.5em',
              borderRadius: '0.25em',
            },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
