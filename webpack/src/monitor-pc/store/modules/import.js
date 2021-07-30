import { historyList, historyDetail,
  importConfig, addMonitorTarget, exportPackage } from '../../../monitor-api/modules/export_import'
import { transformDataKey } from '../../../monitor-common/utils/utils'

export const SET_CURRENT_HIS_REQ = 'SET_CURRENT_HIS_REQ'
const state = {
  cancelReq: null
}
const getters = {
  cancelReq(state) {
    return state.cancelReq
  }
}
const mutations = {
  [SET_CURRENT_HIS_REQ](state, req) {
    state.cancelReq = req
  }
}
const actions = {
  /**
     * 历史列表页
     * @param {*} commit
     * @param {*} params
     */
  async getHistoryList() {
    const list = await historyList().catch(() => [])
    if (!list) {
      return []
    }
    return transformDataKey(list)
  },
  /**
     * 开始导入
     * @param {*} commit
     * @param {*} params
     */
  async handleImportConfig(store, params) {
    const importParams = {
      uuid_list: params.uuids
    }
    // 历史ID存在就丢给后端
    if (params.historyId) {
      importParams.import_history_id = params.historyId
    }
    const data = await importConfig(importParams).catch(() => null)
    if (!data) {
      return null
    }
    return transformDataKey(data)
  },
  /**
     * 获取历史详情
     * @param {*} commit
     * @param {*} id
     */
  async getHistoryDetail({ commit }, id) {
    const cancelFn = (c) => {
      commit(SET_CURRENT_HIS_REQ, c)
    }
    const data = await historyDetail({ import_history_id: id }, { needCancel: true, cancelFn }).catch(() => ({
      configList: []
    }))
    return transformDataKey(data)
  },
  /**
     * 统一添加监控目标
     * @param {*} commit
     * @param {*} params
     */
  async addMonitorTarget(store, params) {
    const data = await addMonitorTarget(params)
    return data
  },
  /**
     * 上传文件
     * @param {*} commit
     * @param {*} params
     */
  async exportPackage(store, params) {
    const data = await exportPackage(params).catch(err => err)
    return transformDataKey(data)
  }
}
export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
