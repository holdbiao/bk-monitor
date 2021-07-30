import os from 'os'
import fs from 'fs'
import path from 'path'
import tsImportPluginFactory from 'ts-import-plugin'
import { ServiceConfig } from '../../typings/config'
const appDirectory = fs.realpathSync(process.cwd())
const resolve = (relativePath: string) => path.resolve(appDirectory, relativePath)
const cpus = os.cpus().length
export default (config: ServiceConfig) => [
  {
    test: /\.tsx?$/,
    exclude: [/[\\/]node_modules[\\/]/, /[\\/]toastui-editor/, /[\\/]china\.js$/],
    use: [
      {
        loader: 'babel-loader',
        options: {
          presets: [['@babel/preset-env']],
          cacheDirectory: './webpack_cache/'
        }
      },
      {
        loader: 'ts-loader',
        options: Object.assign(
          {}, {
            transpileOnly: true,
            appendTsSuffixTo: [/\.vue$/],
            compilerOptions: {
              module: 'es2015'
            }
          },
          config.mobile ? {
            getCustomTransformers: (): {} => ({
              before: [
                tsImportPluginFactory({
                  libraryName: 'vant',
                  libraryOverride: false,
                  libraryDirectory: 'es',
                  resolveContext: [config.appDir],
                  style: true
                })
              ]
            })
          } : {}
        )
      }
    ]
  },
  {
    test: /\.js$/,
    exclude: [/[\\/]node_modules[\\/]/, /[\\/]toastui-editor/, /[\\/]china\.js$/],
    use: [
      {
        loader: 'thread-loader',
        options: {
          workers: cpus - 1
        }
      },
      {
        loader: 'babel-loader',
        options: {
          presets: [['@babel/preset-env']],
          cacheDirectory: './webpack_cache/'
        }
      }
    ].filter(Boolean),
    include: [
      resolve('src')
    ]
  }
]
