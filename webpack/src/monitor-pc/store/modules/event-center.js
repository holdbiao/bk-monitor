import { listSearchItem, listEvent, detailEvent,
  listAlertNotice, detailAlertNotice,
  listEventLog, stackedChart, listConvergeLog } from '../../../monitor-api/modules/alert_events'
import { transformDataKey } from '../../../monitor-common/utils/utils'
export const SET_SEARCH_LIST = 'SET_SEARCH_LIST'
const state = {
  searchList: []
}
const mutations = {
  [SET_SEARCH_LIST](state, data) {
    state.searchList = data
  }
}

const actions = {
  async getSearchList({ commit }, params) {
    const data = await listSearchItem(params).catch(() => [])
    const list = data.map(item => ({ ...item, multiable: true }))
    // list.unshift({
    //     id: 'bk_biz_id',
    //     name: '业务名',
    //     multiable: true,
    //     children: rootGetters.bizList.map(set => ({ id: set.id, name: set.text }))
    // })
    commit(SET_SEARCH_LIST, list)
  },
  async getEventList({ rootGetters }, params) {
    const list = await listEvent(params).catch(() => ({
      event_list: [],
      statistics_data: {}
    }))
    if (params.export) return list
    const tagData = {
      anomalyCount: list.statistics_data?.abnormal_count || 0,
      shieldAnomalyCount: list.statistics_data?.shield_abnormal_count || 0,
      total: list.statistics_data?.total || 0,
      allCount: list.statistics_data?.all_count || 0
    }
    const eventList = list.event_list?.map((item) => {
      const bizItem = rootGetters.bizList.find(set => `${set.id}` === `${item.bk_biz_id}`) || {}
      return {
        id: item.id,
        bizId: bizItem.id,
        bizName: bizItem.text || '',
        anomalyCount: item.anomaly_count,
        duration: item.duration,
        beginTime: item.begin_time,
        children: item.children,
        strategyName: item.strategy_name,
        isAck: item.is_ack,
        ackMessage: item.ack_message,
        eventMessage: item.event_message,
        eventStatus: item.event_status,
        alertStatus: item.alert_status,
        level: item.level,
        collapse: false,
        isShielded: item.is_shielded,
        shieldType: item.shield_type
      }
    })
    return {
      tagData,
      eventList
    }
  },
  async getEventDetailData(store, params) {
    const data = await detailEvent(params).catch(() => null)
    if (!data) {
      return data
    }
    return transformDataKey(data)
  },
  async getNoticeDetail(store, params) {
    const list = await listAlertNotice(params).catch(() => [])
    return list.map(item => transformDataKey(item))
  },
  async getNoticeTableDetail(store, params) {
    const data = await detailAlertNotice(params).catch(() => ({}))
    return transformDataKey(data)
  },
  async getlistEventLog(store, params) {
    const data = await listEventLog(params)
    data.forEach((item) => {
      item.logIcon = `icon-mc-alarm-${item.operate.toLocaleLowerCase()}`
      if (item.operate === 'RECOVER') {
        item.logIcon += 'ed'
      }

      if (item.operate === 'ANOMALY_NOTICE') {
        item.logIcon = 'icon-mc-alarm-notice'
      }

      if (item.operate === 'CLOSE') {
        item.logIcon = 'icon-mc-alarm-closed'
      }

      if (item.is_multiple) {
        item.collapse = true
        item.expandTime = `${item.begin_time} 至 ${item.time}`
        item.expand = false
      } else {
        item.collapse = false
        item.expand = true
      }
      item.border = false
      item.show = true
      item.expandDate = ''
    })
    return transformDataKey(data)
  },
  // 获取变化趋势图数据
  async getChartData(store, params) {
    const data = await stackedChart(params).catch(() => ({}))
    return transformDataKey(data)
  },
  async getListConvergeLog(store, params) {
    const data = await listConvergeLog(params).catch(() => [])
    data.forEach((item) => {
      item.operate === 'ANOMALY_NOTICE'
        ? item.logIcon = 'icon-mc-alarm-notice'
        : item.logIcon = `icon-mc-alarm-${item.operate.toLocaleLowerCase()}`

      if (item.operate === 'RECOVER') {
        item.logIcon += 'ed'
      }
      item.collapse = false
      item.expand = true
      item.border = false
      item.show = true
      item.expandTime = ''
    })
    return transformDataKey(data)
  }
}

const getters = {
  searchList(state) {
    return state.searchList
  }
}

export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters
}
