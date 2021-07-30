import { noticeGroupList } from '../../../monitor-api/modules/notice_group'
import { getUnitList, getDimensionValues, strategyConfig,
  getScenarioList, getIndexSetList, getLogFields,
  noticeVariableList, renderNoticeTemplate, getUnitInfo } from '../../../monitor-api/modules/strategies'
import { getVariableValue } from '../../../monitor-api/modules/grafana'
import Vue from 'vue'
export const SET_LOADING = 'SET_LOADING'
export const SET_LOG_LOADING = 'SET_LOG_LOADING'
export const SET_GROUP_LIST = 'SET_GROUP_LIST'
export const SET_DIMENSION_VALUE_MAP = 'SET_DIMENSION_VALUE_MAP'
export const SET_STRATEGY_PARAMS = 'SET_STRATEGY_PARAMS'
export const SET_SCENARIO_LIST = 'SET_SCENARIO_LIST'
export const SET_EMPTY_DIMENSION = 'SET_EMPTY_DIMENSION'

const state = {
  groupList: [],
  scenarioList: [],
  dimensionValueLoading: false,
  logDimensionLoading: false,
  dimensionsValueMap: {

  },
  strategyParams: null,
  algorithmOptionMap: {
    Threshold: '静态阈值',
    SimpleRingRatio: '环比策略（简易）',
    SimpleYearRound: '同比策略（简易）',
    AdvancedRingRatio: '环比策略（高级）',
    AdvancedYearRound: '同比策略（高级）',
    PartialNodes: '部分节点数',
    YearRoundAmplitude: '同比振幅',
    RingRatioAmplitude: '环比振幅',
    YearRoundRange: '同比区间',
    IntelligentDetect: '智能异常检测'
  },
  uptimeCheckMap: {
    available: 'Threshold',
    task_duration: 'Threshold',
    message: 'PartialNodes',
    response_code: 'PartialNodes'
  }
}
const mutations = {
  SET_LOADING(state, v) {
    state.dimensionValueLoading = v
  },
  SET_LOG_LOADING(state, v) {
    state.logDimensionLoading = v
  },
  SET_GROUP_LIST(state, data) {
    state.groupList = data
  },
  SET_DIMENSION_VALUE_MAP(state, { id, data }) {
    state.dimensionsValueMap[id] = data
  },
  SET_STRATEGY_PARAMS(state, params) {
    state.strategyParams = Object.assign({}, params)
  },
  SET_SCENARIO_LIST(state, data = []) {
    state.scenarioList = data
  },
  SET_EMPTY_DIMENSION(state) {
    state.dimensionsValueMap = {}
  }
}
const actions = {
  async getNoticeGroupList({ commit }) {
    await noticeGroupList().then((data) => {
      const groupData = data.map(item => ({
        id: item.id,
        name: item.name,
        receiver: item.notice_receiver.map(rec => rec.display_name)
      }))
      commit(SET_GROUP_LIST, groupData)
    })
  },
  async getDimensionValueList({ commit }, params) {
    // commit(SET_LOADING, needLoading)
    await getDimensionValues(params, { needRes: true }).then(({ data, tips }) => {
      if (tips?.length) {
        Vue.prototype.$bkMessage({
          theme: 'warning',
          message: tips
        })
      }
      commit(SET_DIMENSION_VALUE_MAP, {
        id: params.field,
        data: Array.isArray(data) ? data : []
      })
    })
      .catch(() => [])
  },
  async getVariableValueList({ commit, rootGetters }, params) {
    if (params.params.data_source_label === 'custom' && params.params.data_type_label === 'event') {
      // eslint-disable-next-line max-len
      params.params.result_table_id = `${params.bk_biz_id || rootGetters.bizId}_bkmonitor_event_${params.params.result_table_id}`
      params.params.metric_field = '_index'
    }

    await getVariableValue(params, { needRes: true }).then(({ data, tips }) => {
      if (tips?.length) {
        Vue.prototype.$bkMessage({
          theme: 'warning',
          message: tips
        })
      }
      const result = Array.isArray(data) ? data.map(item => (
        { name: item.label, id: item.value }
      )) : []
      const { field } = params.params
      commit(SET_DIMENSION_VALUE_MAP, {
        id: field,
        data: result
      })
    })
      .catch(() => [])
  },
  async addStrategyConfig(store, params) {
    await strategyConfig(params)
  },
  // 获取索引集数据
  async getIndexSetList(store, params) {
    const data = await getIndexSetList(params).catch(() => null)
    return data
  },
  // 获取日志关键字维度
  async getLogFields({ commit }, params) {
    commit(SET_LOG_LOADING, true)
    const data = await getLogFields(params).catch(() => ({
      dimension: [],
      condition: []
    }))
      .finally(() => {
        commit(SET_LOG_LOADING, false)
      })
    return data
  },
  // 获取策略模板变量列表
  async getNoticeVariableList({ rootGetters }) {
    const data = await noticeVariableList({ bk_biz_id: rootGetters.bizId }).catch(() => [])
    return data
  },
  // 获取策略模板预览
  async getRenderNoticeTemplate({ rootGetters }, params) {
    const data = await renderNoticeTemplate({
      ...params,
      bk_biz_id: rootGetters.bizId
    }).catch(() => [])
    return data
  },
  async getScenarioList({ commit }) {
    await getScenarioList().then((data) => {
      commit(SET_SCENARIO_LIST, data)
    })
  },
  // 通过id获取单位信息
  async getUnitData({ rootGetters }, { unitId }) {
    const data = await getUnitInfo({
      unit_id: unitId,
      bk_biz_id: rootGetters.bizId
    }).catch(() => ({}))
    return data
  },
  async getUnitList(store, params) {
    const arr = await getUnitList(params).catch(() => [])
    return arr
  }
}
const getters = {
  groupList(state) {
    return state.groupList
  },
  scenarioList(state) {
    return state.scenarioList
  },
  dimensionValueLoading(state) {
    return state.dimensionValueLoading
  },
  logDimensionLoading(state) {
    return state.logDimensionLoading
  },
  dimensionsValueMap(state) {
    return state.dimensionsValueMap
  },
  strategyParams(state) {
    return state.strategyParams
  },
  algorithmOptionMap(state) {
    return state.algorithmOptionMap
  },
  uptimeCheckMap(state) {
    return state.uptimeCheckMap
  }
}
export default {
  namespaced: true,
  state,
  mutations,
  getters,
  actions
}
