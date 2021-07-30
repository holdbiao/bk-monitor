/* eslint-disable new-cap */
import { VuexModule, Action, Module, getModule } from 'vuex-module-decorators'
import {
  getEventGraphView,
  getEventDetail
} from '../../../monitor-api/modules/mobile_event'
import { transformDataKey } from '../../../monitor-common/utils/utils'
import store from '../store'

@Module({ dynamic: true, name: 'event', namespaced: true, store })
class Event extends VuexModule {
  // 获取图表数据
  @Action
  async getChartData(payload) {
    const data = await getEventGraphView(payload).catch(() => ({}))
    return data
  }

  // 获取事件详情
  @Action
  async getEventDetail(payload) {
    const data = await getEventDetail({
      event_id: payload.id || -1
    }).catch(() => ({}))
    return transformDataKey(data)
  }
}

export default getModule(Event, store)
