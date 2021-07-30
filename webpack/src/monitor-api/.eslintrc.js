module.exports = {
  root: true,
  extends: [
    '@blueking/eslint-config/js' // Uses the recommended rules from the @typescript-eslint/eslint-plugin
  ],
  env: {
    browser: true,
    es6: true,
    node: true
  },
  globals: {
    Atomics: 'readonly',
    SharedArrayBuffer: 'readonly',
    NODE_ENV: true,
    SITE_URL: true,
    __webpack_public_path__: true
  }
}
