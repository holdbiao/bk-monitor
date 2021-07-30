import { Component, Vue } from 'vue-property-decorator'
import authorityStore from '../store/modules/authority'
Component.registerHooks([
  'beforeRouteEnter'
])
// eslint-disable-next-line new-cap
export default (authMap: {[propsName: string]: string}) => Component(class authorityMixin extends Vue {
  public authority: {[propsName: string]: boolean} = {}
  public constructor() {
    super()
    this.authority = Object.keys(authMap).reduce((pre: any, cur: string) => (pre[cur] = false, pre), {})
  }
  public beforeRouteEnter(to: any, from: any, next: any) {
    next((vm: any) => {
      const authorityMap: any = authMap || (to.meta.authority  && to.meta.authority.map ? to.meta.authority.map : false)
      const isSpecialEvent =  ['event-center', 'event-center-detail'].includes(to.name)
      && location.search.indexOf('specEvent') > -1
      authorityMap && vm.handleInitPageAuthority(
        Array.from((new Set(Object.values(authorityMap).flat(2))))
        , isSpecialEvent
      )
    })
  }
  // 初始化通用页面权限
  public async handleInitPageAuthority(actionList: string[], isSpecialEvent: boolean) {
    const data: {actionId: string, isAllowed: boolean}[] = await authorityStore.checkAllowedByActionIds({
      action_ids: actionList
    })
    Object.entries(authMap).forEach((entry) => {
      const [key, value] = entry
      const isViewAuth =  key.indexOf('VIEW_AUTH') > -1
      if (Array.isArray(value)) {
        const filterData = data.filter(item => value.includes(item.actionId))
        const hasAuth = filterData.every(item => item.isAllowed)
        filterData.length && (this.$set(this.authority, key, isViewAuth ? isSpecialEvent || hasAuth : hasAuth))
      } else {
        const curEntry = data.find(item => item.actionId === value)
        curEntry && (this.$set(this.authority, key, isViewAuth
          ? isSpecialEvent || curEntry.isAllowed
          : curEntry.isAllowed))
      }
    })
  }
  // 显示申请权限的详情
  public handleShowAuthorityDetail(actionId: string) {
    authorityStore.getAuthorityDetail(actionId || this.$route.meta.authority?.map?.MANAGE_AUTH)
  }
})
