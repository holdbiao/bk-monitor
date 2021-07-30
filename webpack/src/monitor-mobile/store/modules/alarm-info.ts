/* eslint-disable new-cap */
import { VuexModule, Action, Module, getModule } from 'vuex-module-decorators'
import {
  getAlarmDetail,
  getEventGraphView,
  getEventList
} from '../../../monitor-api/modules/mobile_event'
import { transformDataKey } from '../../../monitor-common/utils/utils'
import store from '../store'

@Module({ dynamic: true, name: 'alarm', namespaced: true, store })
class Alarm extends VuexModule {
  @Action
  async getAlarmInfo() {
    store.commit('app/setPageLoading', true)
    const data = await Promise.all([getAlarmDetail({
      alert_collect_id: store.state.app.collectId
    }).catch(() => []), this.getEventNum()])
    store.commit('app/setPageLoading', false)
    return transformDataKey(data[0])
  }

  @Action
  async getChartData(payload) {
    const data = await getEventGraphView(payload).catch(() => ({}))
    return data
  }

  @Action
  async getEventNum() {
    const data = await getEventList({
      bk_biz_id: store.state.app.bizId,
      only_count: true
    }).catch(() => false)
    store.commit('app/setAlarmNum', data?.count ? data.count.strategy : 0)
  }
}

export default getModule(Alarm, store)
