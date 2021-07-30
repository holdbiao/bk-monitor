import { shieldSnapshot } from '../../../monitor-api/modules/alert_events'
import { transformDataKey } from '../../../monitor-common/utils/utils'

const state = {}
const getters = {}
const mutations = {}
const actions = {
  async shieldSnapshot(store, params) {
    const obj = await shieldSnapshot(params).catch(() => ({}))
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
