import { getTopoTree, getLabel, getServiceCategory } from '../../../monitor-api/modules/commons'

export const SET_TREE_DATA = 'SET_TREE_DATA'
export const SET_DATA_OBJECT = 'SET_DATA_OBJECT'
export const SET_SERVICE_CATEGORY = 'SET_SERVICE_CATEGORY'
const mutations = {
  SET_TREE_DATA(state, data) {
    state.treeData = data
  },
  SET_DATA_OBJECT(state, data) {
    state.dataObject = data
  },
  SET_SERVICE_CATEGORY(state, data) {
    state.serviceCategory = data
  }
}
const state = {
  treeData: [],
  dataObject: [],
  serviceCategory: []
}
const actions = {
  async getTopoTree({ commit }, params) {
    const arr = await getTopoTree(params).catch(() => [])
    commit(SET_TREE_DATA, arr)
    return arr
  },
  async getDataObject({ commit }, params) {
    const arr = await getLabel(params).catch(() => [])
    commit(SET_DATA_OBJECT, arr)
    return arr
  },
  async getServiceCategory({ commit }) {
    const arr = await getServiceCategory().catch(() => [])
    commit(SET_SERVICE_CATEGORY, arr)
    return arr
  }
}
const getters = {
  treeData(state) {
    return state.treeData
  },
  dataObject(state) {
    return state.dataObject
  },
  serviceCategory(state) {
    return state.serviceCategory
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
