import { VuexModule, Module, getModule, Action, Mutation  } from 'vuex-module-decorators'
import { getAuthorityMeta, getAuthorityDetail, checkAllowedByActionIds } from '../../../monitor-api/modules/iam'
import store from '../store'
import { transformDataKey } from '../../../monitor-common/utils/utils'

// eslint-disable-next-line new-cap
@Module({ name: 'authority', dynamic: true, namespaced: true, store })
class Authority extends VuexModule {
  public authorityMeta: any = []
  public showAuthortyDialog = false
  public dialogLoading = false
  public authApplyUrl = ''
  public authDetail: any = {}
  public get showDialog() {
    return this.showAuthortyDialog
  }
  public get loading() {
    return this.dialogLoading
  }
  public get applyUrl() {
    return this.authApplyUrl
  }
  public get authorityDetail() {
    return this.authDetail
  }
  @Mutation
  public setAuthorityMeta(data: any) {
    this.authorityMeta = data
  }
  @Mutation
  public setShowAuthortyDialog(data: boolean) {
    this.showAuthortyDialog = data
  }
  @Mutation
  public setDialogLoading(data: boolean) {
    this.dialogLoading = data
  }
  @Mutation
  public setApplyUrl(data: string) {
    this.authApplyUrl = data
  }
  @Mutation
  public setAuthorityDetail(data: any) {
    this.authDetail = data
  }
  @Action // 获取系统所有权限对应表
  public async getAuthorityMeta() {
    const data =  await getAuthorityMeta().catch(() => [])
    this.setAuthorityMeta(transformDataKey(data))
  }
  @Action // 通过actionId获取对应权限及依赖的权限的详情，及申请权限的跳转Url
  public async getAuthorityDetail(actionId: string | string[]) {
    this.setDialogLoading(true)
    this.setShowAuthortyDialog(true)
    const res = await this.handleGetAuthDetail(actionId)
    const data = transformDataKey(res)
    this.setApplyUrl(data.applyUrl)
    this.setAuthorityDetail(data.authorityList)
    this.setDialogLoading(false)
  }
  @Action
  public async handleGetAuthDetail(actionId: string | string[]) {
    const res =  await getAuthorityDetail({
      action_ids: Array.isArray(actionId)
        ? actionId
        : [actionId] }).catch(() => ({ applyUrl: '', authorityList: {} }))
    return res
  }
  @Action
  public showAuthorityDetail(res: any) {
    this.setDialogLoading(true)
    this.setShowAuthortyDialog(true)
    const data = transformDataKey(res)
    this.setApplyUrl(data.data.applyUrl)
    this.setAuthorityDetail(data.permission)
    this.setDialogLoading(false)
  }
  @Action // 通过actionIds获取对应权限是否放行
  public async checkAllowedByActionIds(params: any) {
    const data =  await checkAllowedByActionIds({
      ...params,
      bk_biz_id: store.getters.bizId
    }).catch(() => [])
    return transformDataKey(data)
  }
}

export default getModule(Authority)
