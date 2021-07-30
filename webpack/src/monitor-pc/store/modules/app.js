export const SET_TITLE = 'SET_TITLE'
export const SET_BACK = 'SET_BACK'
export const SET_BIZ_ID = 'SET_BIZ_ID'
export const SET_HANDLE_BACK = 'SET_HANDLE_BACK'
export const SET_APP_STATE = 'SET_APP_STATE'
export const SET_NAV_ID = 'SET_NAV_ID'
export const SET_NAV_TITLE = 'SET_NAV_TITLE'
export const SET_MAIN_LOADING = 'SET_MAIN_LOADING'
export const SET_MESSAGE_QUEUE = 'SET_MESSAGE_QUEUE'
export const SET_LOGIN_URL = 'SET_LOGIN_URL'

const state = {
  title: '',
  csrfCookieName: window.csrf_cookie_name || 'enterprise_monitor_csrftoken',
  needBack: false,
  bizId: '',
  bizList: [],
  userName: '',
  isSuperUser: false,
  navId: '',
  navTitle: '',
  enableMessageQueue: false,
  messageQueueDSN: '',
  mcMainLoading: false, // 框架内容loading
  maxAvailableDurationLimit: 3000, // 拨测超时设置最大值
  upgradeAllowed: false, // 是否允许显示配置升级页面
  cmdbUrl: '',
  bkLogSearchUrl: '', // 日志检索url
  bkUrl: '',
  bkNodemanHost: '', // 节点管理域名
  loginUrl: '', // 登录Url
  navToggle: localStorage.getItem('navigationToogle') === 'true',
  collectingConfigFileMaxSize: null, // 插件参数文件大小限制单位M
  enable_cmdb_level: false // 是否启用功能视图勾选Topo节点的功能开关
}

const mutations = {
  [SET_TITLE](state, title) {
    state.title = title
  },
  [SET_BACK](state, back) {
    state.needBack = back
  },
  [SET_BIZ_ID](state, id) {
    state.bizId = id
  },
  [SET_APP_STATE](state, data) {
    state.userName = data.userName
    state.bizId = data.bizId
    state.isSuperUser = data.isSuperUser
    state.bizList = data.bizList.slice()
    state.siteUrl = data.siteUrl
    state.enableMessageQueue = data.enableMessageQueue
    state.messageQueueDSN = data.messageQueueDSN
    state.maxAvailableDurationLimit = data.maxAvailableDurationLimit
    state.upgradeAllowed = data.upgradeAllowed
    state.cmdbUrl = data.cmdbUrl
    state.bkLogSearchUrl = data.bkLogSearchUrl
    state.bkUrl = data.bkUrl
    state.bkNodemanHost = data.bkNodemanHost
    state.collectingConfigFileMaxSize = data.collectingConfigFileMaxSize
    state.enable_cmdb_level = data.enable_cmdb_level
  },
  [SET_NAV_ID](state, id) {
    state.navId = id
  },
  [SET_NAV_TITLE](state, title) {
    state.navTitle = title
  },
  [SET_MAIN_LOADING](state, loading) {
    state.mcMainLoading = loading
  },
  [SET_MESSAGE_QUEUE](state, data) {
    state.enableMessageQueue = data.enable || false
    state.messageQueueDSN = data.dsn || ''
  },
  [SET_LOGIN_URL](state, url) {
    state.loginUrl = url
  },
  setNavToggle(state, status) {
    state.navToggle = status
  }
}

export default {
  namespaced: true,
  state,
  mutations
}
