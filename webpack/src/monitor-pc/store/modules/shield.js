import { frontendShieldDetail } from '../../../monitor-api/modules/shield'
import { transformDataKey } from '../../../monitor-common/utils/utils'

const state = {}
const getters = {}
const mutations = {}
const actions = {
  async frontendShieldDetail(store, params) {
    const obj = await frontendShieldDetail(params).catch(() => ({}))
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
