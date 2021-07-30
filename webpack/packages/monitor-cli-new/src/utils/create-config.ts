/* eslint-disable max-len */
/* eslint-disable no-nested-ternary */
import path from 'path'
import fs from 'fs'
import { ServiceConfig, BundleOptions } from '../typings/config'
export const appDirectory = fs.realpathSync(process.cwd())
export const resolveApp = (relativePath: string): string => path.resolve(appDirectory, relativePath || '.')

export default async function ({ mobile, analyze, production, email }: BundleOptions): Promise<ServiceConfig> {
  const commonConfig = {
    mobile,
    analyze,
    email,
    env: {
      process: {
        env: {
          NODE_ENV: JSON.stringify(!production ? 'development' : 'production')
        }
      }
    },
    dist: resolveApp('./dist'),
    appDir: resolveApp('./src/'),
    appIndex: resolveApp('./src/index.js'),
    appIndexHtml: email ? resolveApp('./email.html') : !production ? resolveApp('./index.html') : resolveApp('./index.ejs')
  }
  return commonConfig
}
