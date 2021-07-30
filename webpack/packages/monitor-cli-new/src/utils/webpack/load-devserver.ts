import { Configuration  } from 'webpack-dev-server'
export default (): Configuration => ({
  host: 'http://localhost',
  port: 7001,
  proxy: {

  },
  hot: true,
  publicPath: '/',
  open: true,
  noInfo: true,
  stats: 'errors-only' as any,
  watchContentBase: false,
  disableHostCheck: true
})
