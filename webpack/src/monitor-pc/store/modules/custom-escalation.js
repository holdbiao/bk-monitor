import { getScenarioList } from '../../../monitor-api/modules/strategies'
import { customTimeSeriesGraphPoint, proxyHostInfo, queryCustomEventGroup, getCustomEventGroup, customTimeSeriesDetail, customTimeSeriesList, modifyCustomEventGroup, modifyCustomTimeSeries, deleteCustomEventGroup, deleteCustomTimeSeries, validateCustomEventGroupName, validateCustomTsGroupName, getCustomTimeSeriesLatestDataByFields } from '../../../monitor-api/modules/custom_report'
import { transformDataKey } from '../../../monitor-common/utils/utils'

const actions = {
  //  获取监控对象列表
  async getScenarioList() {
    const data = await getScenarioList().catch(_ => [])
    return data
  },

  //  获取自定义指标列表
  async getCustomTimeSeriesList({ commit }, params) {
    const data = await customTimeSeriesList(params).catch(() => ({ list: [], total: 0 }))
    return transformDataKey(data)
  },

  //  获取自定义指标详情
  async getCustomTimeSeriesDetail({ commit }, params) {
    const data = await customTimeSeriesDetail(params).catch(() => ({}))
    return data
  },

  //  编辑自定义指标配置
  async editCustomTime({ commit }, params) {
    const data = await modifyCustomTimeSeries(params).catch(() => false)
    return transformDataKey(data)
  },

  //  删除自定义指标
  async deleteCustomTimeSeries({ commit }, params) {
    const data = await deleteCustomTimeSeries(params).then(() => true)
      .catch(() => false)
    return transformDataKey(data)
  },

  //  获取云区域proxy信息
  async getProxyInfo({ commit }, params) {
    const data = await proxyHostInfo().catch(_ => [])
    return transformDataKey(data)
  },

  //  获取自定义事件列表
  async getCustomEventList({ commit }, params) {
    const data = await queryCustomEventGroup(params).catch(() => ({ list: [], total: 0 }))
    return transformDataKey(data)
  },

  //  获取自定义事件配置详情
  async getCustomEventDetail({ commit }, params) {
    const data = await getCustomEventGroup(params).catch(() => ({ event_info_list: [] }))
    return data
  },

  //  编辑自定义事件配置
  async editCustomEvent({ commit }, params) {
    const data = await modifyCustomEventGroup(params).catch(() => false)
    return transformDataKey(data)
  },

  //  删除自定义事件配置
  async deleteCustomEvent({ commit }, params) {
    const data = await deleteCustomEventGroup(params).then(() => true)
      .catch(() => false)
    return transformDataKey(data)
  },

  //  校验事件名称
  async validateCustomEventName({ commit }, params) {
    const data = await validateCustomEventGroupName(params).catch((err) => {
      if (err.data && err.data.code === 3314001) {
        return false
      }
      return true
    })
    return transformDataKey(data)
  },

  //  校验事件名称
  async validateCustomTimetName({ commit }, params) {
    const data = await validateCustomTsGroupName(params).catch((err) => {
      if (err.data && err.data.code === 3314001) {
        return false
      }
      return true
    })
    return transformDataKey(data)
  },

  // 获取自定义指标图表
  async customTimeSeriesGraphPoint({ commit }, params) {
    const data = await customTimeSeriesGraphPoint(params).catch(() => ({}))
    return transformDataKey(data)
  },
  async getCustomTimeSeriesLatestDataByFields({ commit }, params) {
    const data = await getCustomTimeSeriesLatestDataByFields(params).catch(() => false)
    return data
  }
}

export default {
  namespaced: true,
  actions
}
