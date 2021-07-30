import { setDefaultDashboard, getDefaultDashboard } from '../../../monitor-api/modules/grafana'

const state = {
  dashboardId: '',
  defaultDashboardId: -1,
  dashboardCheck: '',
  manageAuth: false
}
const getters = {
  curDashboardId(state) {
    return state.dashboardId
  },
  setDashboardButtonStatus(state) {
    if (state.dashboardId) {
      return state.defaultDashboardId !== state.dashboardId ? 1 : 2
    }
    return 0
  },
  dashboardCheck(state) {
    return state.dashboardCheck
  },
  hasManageAuth(state) {
    return state.manageAuth
  }
}

const mutations = {
  setDashboardId(state, id) {
    state.dashboardId = id
  },
  setDefaultDashboardId(state, id) {
    state.defaultDashboardId = id
  },
  setDashboardCheck(state, payload) {
    state.dashboardCheck = payload
  },
  setHasManageAuth(state, payload) {
    state.manageAuth = payload
  }
}

const actions = {
  async setDefaultDashboard({ commit, state, rootState }) {
    const data = await setDefaultDashboard({
      dashboard_uid: state.dashboardId,
      bk_biz_id: rootState.app.bizId
    }).catch(() => false)
    commit('setDefaultDashboardId', data ? state.dashboardId : -1)
    return !!data
  },
  async getDefaultDashboard({ commit, state, rootState }) {
    const data = await getDefaultDashboard({
      bk_biz_id: rootState.app.bizId
    }).catch(() => false)
    commit('setDefaultDashboardId', data ? data.uid : state.defaultDashboardId)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
