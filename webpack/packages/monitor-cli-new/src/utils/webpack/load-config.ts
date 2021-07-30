/* eslint-disable no-param-reassign */
import * as webpack from 'webpack'
import fs from 'fs'
import util from 'util'
import path from 'path'
import { merge } from 'webpack-merge'
import createWebpackConfig from './create-config'
import createCustomConfig from '../create-config'
import { BundleOptions } from '../../typings/config'
const accessPromise = util.promisify(fs.access)

type WebpackConfigurationGetter = (options: BundleOptions) => Promise<webpack.Configuration>;
export type CustomWebpackConfigurationGetter = (
  originalConfig: webpack.Configuration,
  options: any
) => webpack.Configuration;


export const loadWebpackConfig: WebpackConfigurationGetter = async (option: BundleOptions) => {
  const customConfig = await createCustomConfig(option)
  const baseConfig = createWebpackConfig(customConfig)
  const customWebpackPath = path.resolve(process.cwd(), 'webpack.config.js')

  try {
    await accessPromise(customWebpackPath)
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const customConfig = await require(customWebpackPath)
    const configGetter = customConfig.getWebpackConfig || customConfig
    if (typeof configGetter === 'function') {
      return (configGetter as CustomWebpackConfigurationGetter)(baseConfig, option)
    }
    return merge(baseConfig, configGetter)
  } catch (err) {
    if (err.code === 'ENOENT') {
      return baseConfig
    }
    throw err
  }
}
