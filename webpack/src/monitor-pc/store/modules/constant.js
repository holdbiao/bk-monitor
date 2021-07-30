const state = {
  eventStatusMap: {
    30: 'ABNORMAL', // 异常事件
    20: 'RECOVERED', // 已恢复
    10: 'CLOSED' // 已恢复
  },
  eventLevelMap: {
    1: '致命',
    2: '预警',
    3: '提醒'
  }
}

const getters = {
  eventStatusMap(state) {
    return state.eventStatusMap
  },
  eventLevelMap(state) {
    return state.eventLevelMap
  }
}

export default {
  namespaced: true,
  state,
  getters
}
