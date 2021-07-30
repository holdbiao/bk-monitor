import webpack from 'webpack'
import WebpackDevServer from 'webpack-dev-server'
import chalk from 'chalk'
import { loadWebpackConfig } from './webpack/load-config'
import { BundleOptions } from '../typings/config'

export const bundleTask = async ({ production, mobile, email,  analyze = false }: BundleOptions) => {
  const webpackConfig = await loadWebpackConfig({ production, mobile, analyze, email })
  !production && WebpackDevServer.addDevServerEntrypoints(webpackConfig, webpackConfig.devServer)
  const compiler = webpack(webpackConfig)
  const webpackPromise = new Promise<void>((resolve, reject) => {
    if (!production) {
      compiler.hooks.invalid.tap('invalid', () => {
        console.log('Compiling...')
      })
      const devServer = new WebpackDevServer(compiler, webpackConfig.devServer)
      devServer.listen(webpackConfig.devServer.port || 7000, webpackConfig.devServer.host || '127.0.0.1', (err) => {
        if (err) {
          return console.error(err)
        }
        console.log(chalk.cyan('Starting the development server...\n'))
      })
      resolve()
    } else {
      compiler.run((err: Error, stats: webpack.Stats) => {
        if (err) {
          reject(err.message)
          return
        }
        if (stats.hasErrors()) {
          stats.compilation.errors.forEach((e) => {
            console.log(e.message)
          })

          reject('Build failed')
        }
        console.log('\n', stats.toString({ colors: true }), '\n')
        resolve()
      })
    }
  })
  return webpackPromise
}
