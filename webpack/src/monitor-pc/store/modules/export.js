import { getAllConfigList } from '../../../monitor-api/modules/export_import'
import { transformDataKey } from '../../../monitor-common/utils/utils'

const state = {}
const getters = {}
const mutations = {}
const actions = {
  async getAllExportList(store, params) {
    const obj = await getAllConfigList(params).catch(() => ({
      collect_config_list: [],
      strategy_config_list: [],
      view_config_list: []
    }))
    return transformDataKey(obj)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
