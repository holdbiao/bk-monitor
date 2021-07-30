import TerserPlugin from 'terser-webpack-plugin'
import CssMinimizerPlugin from 'css-minimizer-webpack-plugin'
export default (isProd: boolean)  => ({
  minimize: isProd,
  runtimeChunk: isProd ? 'multiple' : 'single',
  moduleIds: 'deterministic',
  minimizer: [
    new CssMinimizerPlugin({
      cache: true,
      parallel: true
    }),
    new TerserPlugin({
      exclude: /\.min\.js$/,
      parallel: true
    })
  ],
  splitChunks: {
    chunks: 'all',
    minSize: 30000,
    maxSize: Infinity,
    minRemainingSize: 0,
    minChunks: 1,
    maxAsyncRequests: 10,
    maxInitialRequests: 30,
    automaticNameDelimiter: '~',
    enforceSizeThreshold: 50000,
    cacheGroups: {
      bkMagic: {
        enforce: false,
        chunks: 'all',
        name: 'chunk-bk-magic',
        priority: 20,
        reuseExistingChunk: true,
        test: /\/bk-magic-vue\//
      },
      // monaco: {
      //   enforce: true,
      //   chunks: 'async',
      //   name: 'chunk-monaco',
      //   priority: 20,
      //   reuseExistingChunk: true,
      //   test: (module: any): boolean => /monaco-editor/.test(module.context)
      // },
      vendors: {
        test: /[\\/]node_modules[\\/]/,
        priority: -10,
        reuseExistingChunk: true,
      },
      default: {
        priority: -20,
        minChunks: 2,
        reuseExistingChunk: true
      }
    }
  }
} as any)
