module.exports = {
  root: true,
  extends: [
    '@blueking/eslint-config/js' // Uses the recommended rules from the @typescript-eslint/eslint-plugin
  ],
  rules: {
    '@typescript-eslint/explicit-member-accessibility': 'off',
    'no-useless-constructor': 'off',
    'import/prefer-default-export': 'off'
  },
  env: {
    es6: true,
    node: true,
    jest: false,
    browser: false
  },
  globals: {
    window: false,
    document: false,
    navigator: false
  }
}
