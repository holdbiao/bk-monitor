/* eslint-disable new-cap */
import { VuexModule, Action, Module, getModule, Mutation } from 'vuex-module-decorators'
import { getEventList } from '../../../monitor-api/modules/mobile_event'
import { transformDataKey } from '../../../monitor-common/utils/utils'
import store from '../store'

export interface IEventCenterState {
  allList?: IListItem[];
  filterList?: IListItem[];
  count?: ICount;
  page?: number;
  limit?: number;
  viewList?: IListItem[];
  finished?: boolean;
}
interface ICount {
  shield?: number;
  strategy?: number;
  target?: number;
}
interface IListItem {
  target?: string;
  strategyId?: string;
  name?: string;
  level?: string;
  events: IEventsItem[];
}
interface IEventsItem {
  dimensionMessage: string;
  duration: string;
  eventId: number;
  target?: string;
  strategyName?: string;
}
interface IData {
  count: ICount;
  groups: IListItem[];
}

@Module({ dynamic: true, name: 'eventCenter', namespaced: true, store })
class EventCenter extends VuexModule implements IEventCenterState {
  // type下所有数据
  public allList = []
  // level的所有数据
  public filterList = []
  // 页面显示的列表
  public viewList = []
  // 统计数据
  public count = {}
  // 当前页
  public page = 1
  // 每页条数
  public limit = 10
  // 是否加载完当前分类下的数据
  public finished = false

  // 设置state
  @Mutation
  public setListData(data: IEventCenterState) {
    Object.keys(data).forEach((key) => {
      this[key] = data[key]
    })
  }

  // 增加一页数据
  @Mutation
  public addPage() {
    const start = (this.page - 1) * this.limit
    const end = this.page * this.limit
    if (this.viewList.length < this.filterList.length) {
      const pageList = this.filterList.slice(start, end)
      this.viewList.push(...pageList)
    }
    this.viewList.length >= this.filterList.length && (this.finished = true)
  }

  // 过滤类型数据
  @Mutation
  public getFilterLIst(level: number | string) {
    if (!level) return (this.filterList = this.allList)
    this.filterList = this.allList.filter(item => item.level === +level)
    this.page = 1
  }

  // 接口获取数据
  @Action
  public async getAllList(payload: { level?: number; type?: string }) {
    store.commit('app/setPageLoading', true)
    let data: IData = await getEventList({
      bk_biz_id: store.getters['app/curBizId'],
      type: payload.type
    }).catch(() => [])
    store.commit('app/setPageLoading', false)
    data = transformDataKey(data)
    const list = data.groups
    this.setListData({ allList: list, count: data.count })
    this.getFilterLIst(payload.level)
  }
}

export default getModule(EventCenter)
