/* eslint-disable no-nested-ternary */
const wepack = require('webpack')
const path = require('path')
const fs = require('fs')
const CopyPlugin = require('copy-webpack-plugin')
const MonitorWebpackPlugin = require('./webpack/monitor-webpack-plugin')
const devProxyUrl = 'http://appdev.bktencent.com:9002'
const devHost = 'appdev.bktencent.com'
const loginHost = 'https://paas-dev.bktencent.com'
const devPort = 7001
let devConfig = {
  port: devPort,
  host: devHost,
  devProxyUrl,
  loginHost,
  proxy: {}
}
const monitorPluginConfig = {
  mobileBuildVariates: `
  <script>
      window.site_url = "\${WEIXIN_SITE_URL}"
      window.static_url = "\${WEIXIN_STATIC_URL}"
      window.cc_biz_id = \${BK_BIZ_ID}
      window.user_name = "\${UIN}"
      window.csrf_cookie_name = "\${CSRF_COOKIE_NAME}"
      window.userInfo = {
          username: "\${UIN}",
          isSuperuser: \${IS_SUPERUSER},
      }
      window.graph_watermark = "\${GRAPH_WATERMARK}" == "True" ? true : false
  </script>`,
  pcBuildVariates: `
    <script>
    <%
    import json
    def to_json(val):
        return json.dumps(val)
    %>
    window.platform = {
        "te": \${to_json(PLATFORM.te)},
        "ee": \${to_json(PLATFORM.ee)},
        "ce": \${to_json(PLATFORM.ce)}
    }
    window.cc_biz_list = \${to_json(BK_BIZ_LIST) | n}
    window.app_code = "\${APP_CODE}"
    window.enable_grafana = "\${ENABLE_GRAFANA}" == "True" ? true : false
    window.site_url = "\${SITE_URL}"
    window.static_url = "\${STATIC_URL}"
    window.cc_biz_id = \${BK_BIZ_ID}
    window.csrf_cookie_name = "\${CSRF_COOKIE_NAME}"
    window.doc_host = "\${DOC_HOST}"
    window.job_url = "\${BK_JOB_URL}"
    window.cmdb_url = "\${BK_CC_URL}"
    window.agent_setup_url = "\${AGENT_SETUP_URL}"
    window.user_name = "\${UIN}"
    window.utcOffset = \${UTC_OFFSET}
    window.bk_url = "\${BK_URL}"
    window.bkPaasHost = "\${BK_PAAS_HOST}"
    window.version_log_url = "version_log/"
    window.userInfo = {
        username: "\${UIN}",
        isSuperuser: \${IS_SUPERUSER},
    }
    window.enable_message_queue = \${ENABLE_MESSAGE_QUEUE}
    window.message_queue_dsn = "\${MESSAGE_QUEUE_DSN}"
    window.ce_url = "\${CE_URL}"
    window.max_available_duration_limit = \${MAX_AVAILABLE_DURATION_LIMIT}
    window.upgrade_allowed = \${to_json(UPGRADE_ALLOWED)}
    window.bk_log_search_url = "\${BKLOGSEARCH_HOST}"
    window.bk_nodeman_host = "\${BK_NODEMAN_HOST}"
    window.graph_watermark = "\${GRAPH_WATERMARK}" == "True" ? true : false
    window.mail_report_biz = "\${MAIL_REPORT_BIZ}"
    window.enable_aiops =  \${ENABLE_AIOPS}
    window.collecting_config_file_maxsize = \${COLLECTING_CONFIG_FILE_MAXSIZE}
    window.enable_cmdb_level = "\${ENABLE_CMDB_LEVEL}" == "True" ? true : false
  </script>`
}
if (fs.existsSync(path.resolve(__dirname, './local.settings.js'))) {
  const localConfig = require('./local.settings')
  devConfig = Object.assign({}, devConfig, localConfig)
}
module.exports = (baseConfig, { mobile, production, email = false }) => {
  const distUrl = mobile ? path.resolve('./weixin/') : email ? path.resolve('./email/') : path.resolve('./monitor/')
  const config = baseConfig
  if (!production) {
    config.devServer = Object.assign({}, config.devServer || {}, {
      port: devConfig.port,
      host: devConfig.host,
      proxy: {
        '/rest': {
          target: devConfig.devProxyUrl,
          changeOrigin: true,
          secure: false,
          toProxy: true,
          headers: {
            referer: devConfig.devProxyUrl
          }
        },
        '/api': {
          target: devConfig.devProxyUrl,
          changeOrigin: true,
          headers: {
            referer: devConfig.devProxyUrl
          }
        },
        '/weixin': {
          target: devConfig.devProxyUrl,
          changeOrigin: true,
          secure: false,
          toProxy: true,
          headers: {
            referer: devConfig.devProxyUrl
          }
        },
        '/version_log': {
          target: devConfig.devProxyUrl,
          changeOrigin: true,
          secure: false,
          toProxy: true,
          headers: {
            referer: devConfig.devProxyUrl
          }
        },
        ...devConfig.proxy
      }
    })
    config.plugins.push(new wepack.DefinePlugin(
      {
        process: {
          env: {
            proxyUrl: JSON.stringify(devConfig.devProxyUrl),
            devUrl: JSON.stringify(`${devConfig.host}:${devConfig.port}`),
            loginHost: JSON.stringify(devConfig.loginHost),
            loginUrl: JSON.stringify(`${devConfig.loginHost}/login/`)
          }
        }
      }))
  } else if (!email) {
    config.plugins.push(new CopyPlugin({
      patterns: [
        { from: path.resolve(`./public/${mobile ? 'mobile/' : 'pc/'}`), to: distUrl },
        { from: path.resolve('./public/img'), to: path.resolve(distUrl, './img') }
      ]
    }))
    config.plugins.push(new MonitorWebpackPlugin({ ...monitorPluginConfig, mobile }))
  }
  const appDir = mobile ? './src/monitor-mobile/' : './src/monitor-pc/'
  return {
    ...config,
    output: {
      ...config.output,
      path: distUrl
    },
    entry: {
      ...config.entry,
      main: mobile
        ? './src/monitor-mobile/index.ts'
        : (email ? './src/monitor-pc/email-index.js' : './src/monitor-pc/new-index.js')
    },
    resolve: {
      ...config.resolve,
      alias: {
        vue$: path.resolve(appDir, 'node_modules/vue'),
        moment$: path.resolve(appDir, 'node_modules/moment'),
        'vue-property-decorator$': path.resolve(appDir, 'node_modules/vue-property-decorator'),
        'vue-class-component$': path.resolve(appDir, 'node_modules/vue-class-component'),
        deepmerge$: path.resolve(appDir, 'node_modules/deepmerge'),
        '@': appDir,
        '@router': mobile ? path.resolve('./src/monitor-mobile/router/') : path.resolve('./src/monitor-pc/router/'),
        '@store': mobile ? path.resolve('./src/monitor-mobile/store/') : path.resolve('./src/monitor-pc/store/'),
        '@page': mobile ? path.resolve('./src/monitor-mobile/pages/') : path.resolve('./src/monitor-pc/pages/'),
        '@api': path.resolve('./src/monitor-api/'),
        '@static': path.resolve('./src/monitor-static/'),
        '@common': path.resolve('./src/monitor-common/')
      }
    }
  }
}
