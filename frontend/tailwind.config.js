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
        invert: {
          css: {
            '--tw-prose-body': 'rgb(229, 231, 235)',
            '--tw-prose-headings': 'rgb(255, 255, 255)',
            '--tw-prose-lead': 'rgb(209, 213, 219)',
            '--tw-prose-links': 'rgb(147, 197, 253)',
            '--tw-prose-bold': 'rgb(255, 255, 255)',
            '--tw-prose-counters': 'rgb(209, 213, 219)',
            '--tw-prose-bullets': 'rgb(209, 213, 219)',
            '--tw-prose-hr': 'rgb(75, 85, 99)',
            '--tw-prose-quotes': 'rgb(255, 255, 255)',
            '--tw-prose-quote-borders': 'rgb(75, 85, 99)',
            '--tw-prose-captions': 'rgb(156, 163, 175)',
            '--tw-prose-code': 'rgb(255, 255, 255)',
            '--tw-prose-pre-code': 'rgb(229, 231, 235)',
            '--tw-prose-pre-bg': 'rgb(17, 24, 39)',
            '--tw-prose-th-borders': 'rgb(75, 85, 99)',
            '--tw-prose-td-borders': 'rgb(75, 85, 99)',
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
