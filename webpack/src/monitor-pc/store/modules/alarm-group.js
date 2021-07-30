import { noticeGroupList, noticeGroupDetail
  , getNoticeWay, getReceiver } from '../../../monitor-api/modules/notice_group'
import { transformDataKey } from '../../../monitor-common/utils/utils'

const state = {
  isEdit: false
}

const mutations = {}
const getters = {}
const actions = {
  async noticeGroupList() {
    const arr = await noticeGroupList().catch(() => ([]))
    return transformDataKey(arr)
  },
  async noticeGroupDetail(store, params) {
    const obj = await noticeGroupDetail(params).catch(() => ({}))
    return transformDataKey(obj)
  },
  async getNoticeWay() {
    const arr = await getNoticeWay().catch(() => ([]))
    return transformDataKey(arr)
  },
  async getReceiver() {
    const arr = await getReceiver().catch(() => ([]))
    return arr
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  getters,
  actions
}
