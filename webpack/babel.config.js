module.exports = function (api) {
  // eslint-disable-next-line @typescript-eslint/prefer-optional-chain
  api && api.cache.never()
  const presets = [
    [
      '@babel/preset-env',
      {
        targets: {
          browsers: ['> 1%', 'last 2 versions', 'not ie <= 8'],
          node: 'current'
        },
        useBuiltIns: 'usage',
        corejs: 3,
        debug: false
      }
    ],
    '@vue/babel-preset-jsx'
  ]
  const plugins = [
    '@babel/plugin-transform-runtime',
    [
      'babel-plugin-import-bk-magic-vue', {
        baseLibName: 'bk-magic-vue'
      }
    ],
    [
      'component',
      {
        libraryName: 'element-ui',
        styleLibraryName: 'theme-chalk'
      }
    ],
    ['import', {
      libraryName: 'vant',
      libraryDirectory: 'es',
      style: true
    }, 'vant']
  ]
  return {
    presets,
    plugins
  }
}
