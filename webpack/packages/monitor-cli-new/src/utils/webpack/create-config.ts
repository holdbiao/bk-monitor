import getStyleLoaders from './load-styles'
import getFileLoaders from './load-files'
import getScriptLoaders from './load-script'
import getOptimize from './load-optimize'
import getPlugins from './load-plugin'
import getDevServer from './load-devserver'
import { ServiceConfig } from '../../typings/config'
import { Configuration } from 'webpack-dev-server'
import webpack from 'webpack'
export default (config: ServiceConfig): webpack.Configuration & {devServer?: Configuration} => {
  const isProd = process.env.NODE_ENV === 'production'
  return {
    mode: isProd ? 'production' : 'development',
    entry: { main: config.appIndex },
    output: {
      path: config.dist,
      filename: 'js/[name].[contenthash].js'
    },
    resolve: {
      extensions: ['.js', '.vue', '.json', '.ts', '.tsx'],
      alias: {
        '@': config.appDir
      },
      fallback: {
        fs: false,
        path: require.resolve('path-browserify')
      }
    },
    module: {
      strictExportPresence: true,
      rules: [
        {
          test: /\.vue$/,
          loader: 'vue-loader',
          options: {
            hotReload: !isProd
          }
        },
        {
          oneOf: [
            ...getScriptLoaders(config),
            ...getStyleLoaders(isProd),
            ...getFileLoaders()
          ]
        }
      ]
    },
    cache: isProd ? false : {
      type: 'filesystem'
    },
    optimization: {
      ...getOptimize(isProd)
    },
    plugins: [
      ...getPlugins(isProd, config)
    ].filter(Boolean),
    devServer: Object.assign(isProd ? {} :{
      ...getDevServer()
    }),
    watchOptions: {
      ignored: /node_modules/
    },
    node: {
      global: false,
      __filename: false,
      __dirname: false
    },
    performance: false,
    devtool: isProd ? false : 'eval-source-map',
    stats: {
      children: false,
      warningsFilter: /export .* was not found in/,
      source: false
    }
  }
}
