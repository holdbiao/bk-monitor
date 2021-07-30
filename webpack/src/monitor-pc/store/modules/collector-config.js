import { getLabel } from '../../../monitor-api/modules/commons'

export const SET_ADD_MODE = 'SET_ADD_MODE'
export const SET_ADD_DATA = 'SET_ADD_DATA'
export const SET_OBJECT_TYPE = 'SET_OBJECT_TYPE'
export const SET_INFO_DATA = 'SET_INFO_DATA'

const state = {
  addMode: 'add',
  addData: {},
  objectType: '', // 采集对象类型 SERVICE 为 服务类
  infoData: null // 缓存config-set组件的info
}

const mutations = {
  [SET_ADD_MODE](state, mode) {
    state.addMode = mode
  },
  [SET_ADD_DATA](state, data) {
    state.addData = Object.assign({}, data)
  },
  [SET_OBJECT_TYPE](state, data) {
    state.objectType = data
  },
  [SET_INFO_DATA](state, data) {
    state.infoData = data
  }
}
const getters = {
  addParams(state) {
    return {
      mode: state.addMode,
      data: JSON.parse(JSON.stringify(state.addData))
    }
  },
  getObjectType(state) {
    return state.objectType
  },
  infoData(state) {
    return state.infoData
  }
}
const actions = {
  getCollectorObject() {
    return getLabel({ include_admin_only: false })
  }
}
export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters
}
