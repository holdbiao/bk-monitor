/* eslint-disable new-cap */
import { VuexModule, Module, Mutation } from 'vuex-module-decorators'

export interface IAppState {
  bizId: string | number;
  loading?: boolean;
  collectId: string | number;
  eventId?: string | number;
  alarmNum?: number;
  refresh?: boolean;
  bkBizName: string;
}

@Module({ name: 'app', namespaced: true })
export default class App extends VuexModule implements IAppState {
  public bizId = -1
  public loading = false
  public collectId = -1
  public eventId = -1
  public alarmNum = 0
  public refresh = false
  public bkBizName = ''
  @Mutation
  private SET_APP_DATA(data: IAppState) {
    Object.keys(data).forEach((key) => {
      this[key] = data[key]
    })
  }

  @Mutation
  private SET_EVENT_ID(eventId: number) {
    this.eventId = eventId
  }

  @Mutation
  private setPageLoading(payload: boolean) {
    this.loading = !this.refresh && payload
    !payload && (this.refresh = false)
  }

  @Mutation
  private setRefresh(payload: boolean) {
    this.loading = false
    this.refresh = payload
  }

  @Mutation
  private setAlarmNum(payload: number) {
    this.alarmNum = payload
  }

  @Mutation
  private setDocumentTitle(title) {
    if (title) {
      document.title = title
    }
  }

  get curBizId() {
    return this.bizId
  }

  get alarmCount() {
    return this.alarmNum
  }
}
