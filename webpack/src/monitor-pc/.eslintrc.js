module.exports =  {
  root: true,
  parser: 'vue-eslint-parser',
  parserOptions: {
    ecmaVersion: 2018,
    parser: '@typescript-eslint/parser',
    sourceType: 'module',
    ecmaFeatures: {
      globalReturn: false,
      impliedStrict: false,
      jsx: true
    }
  },
  env: {
    browser: true,
    es6: true,
    node: true
  },
  extends: [
    '@blueking/eslint-config/vue',
    'plugin:vue-i18n/recommended'
  ],
  globals: {
    Atomics: 'readonly',
    SharedArrayBuffer: 'readonly',
    NODE_ENV: true,
    SITE_URL: true,
    __webpack_public_path__: true
  },
  plugins: [
    'vue'
  ],
  rules: {
    'vue-i18n/no-raw-text': 0,
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': ['error'],
    '@typescript-eslint/explicit-member-accessibility': 'off',
    'comma-dangle': ['error', 'never']
  },
  overrides: [
    {
      files: ['*.ts'],
      rules: {
        indent: 'off',
        '@typescript-eslint/indent': ['error', 2]
      }
    },
    {
      files: ['*.tsx'],
      rules: {
        indent: 'off',
        '@typescript-eslint/indent': ['error', 2],
        '@typescript-eslint/explicit-member-accessibility': 'off',
        'new-cap': 'off',
        'max-len': 'off'
      }
    },
    {
      files: ['*.vue'],
      rules: {
        'new-cap': 'off',
        indent: 'off',
        'vue/script-indent': 'off',
        '@typescript-eslint/indent': ['error', 2],
        'max-len': 0,
        'vue/max-len': ['error', {
          code: 120,
          template: 8000,
          tabWidth: 2,
          comments: 8000,
          ignorePattern: '',
          ignoreComments: false,
          ignoreTrailingComments: false,
          ignoreUrls: false,
          ignoreStrings: false,
          ignoreTemplateLiterals: false,
          ignoreRegExpLiterals: false,
          ignoreHTMLAttributeValues: false,
          ignoreHTMLTextContents: false
        }],
        '@typescript-eslint/explicit-member-accessibility': 'off',
        'vue/html-indent': ['error', 2, {
          attribute: 1,
          baseIndent: 1,
          closeBracket: 0,
          alignAttributesVertically: true,
          ignores: []
        }],
        'no-param-reassign': ['warn', {
          props: false
        }]
      }
    },
    {
      files: ['*.js'],
      rules: {
        'no-param-reassign': ['warn', {
          props: false
        }]
      }
    }
  ],
  settings: {
    'vue-i18n': {
      localeDir: './lang/*.json' // extention is glob formatting!
    }
  }
}
