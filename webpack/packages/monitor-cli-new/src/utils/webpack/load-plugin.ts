import webpack from 'webpack'
import VueLoaderPlugin  from 'vue-loader/lib/plugin'
import MiniCssExtractPlugin from 'mini-css-extract-plugin'
import ProgressBarPlugin from 'progress-bar-webpack-plugin'
import HtmlWebpackPlugin from 'html-webpack-plugin'
import { CleanWebpackPlugin } from 'clean-webpack-plugin'
import { BundleAnalyzerPlugin } from 'webpack-bundle-analyzer'
import MomentLocalesPlugin from 'moment-locales-webpack-plugin'
import MonacoWebpackPlugin from 'monaco-editor-webpack-plugin'
import chalk from 'chalk'
export default (isProd: boolean, config: any) => [
  new CleanWebpackPlugin(),
  new webpack.HotModuleReplacementPlugin(),
  new HtmlWebpackPlugin(Object.assign(
    {
      filename: 'index.html',
      template: config.appIndexHtml
    },
    isProd && !config.email ? {
      minify: {
        removeComments: true,
        collapseWhitespace: true,
        removeRedundantAttributes: true,
        useShortDoctype: true,
        removeEmptyAttributes: true,
        removeStyleLinkTypeAttributes: true,
        keepClosingSlash: true,
        minifyJS: true,
        minifyCSS: true,
        minifyURLs: true
      }
    } : {}
  )),

  new ProgressBarPlugin({
    format: `  build [:bar] ${chalk.green.bold(':percent')} (:elapsed seconds)`
  }),
  new webpack.DefinePlugin(config.env),
  new VueLoaderPlugin(),
  isProd ? new MiniCssExtractPlugin({
    filename: isProd ? 'css/[name][contenthash:7].css' : '[name].css',
    ignoreOrder: true
  }) : undefined,
  new webpack.optimize.ModuleConcatenationPlugin(),
  new webpack.optimize.MinChunkSizePlugin({
    minChunkSize: 10000
  }),
  new MomentLocalesPlugin({
    localesToKeep: ['es-us', 'zh-cn'],
  }),
  new webpack.NoEmitOnErrorsPlugin(),
  !config.mobile && !config.email ? new MonacoWebpackPlugin({
    languages: ['shell', 'bat', 'python', 'perl', 'powershell', 'vb', 'json']
  }) : undefined,
  config.analyze ? new BundleAnalyzerPlugin({
    analyzerMode: 'server',
    analyzerHost: '127.0.0.1',
    analyzerPort: 7002
  }) : undefined
].filter(Boolean)
