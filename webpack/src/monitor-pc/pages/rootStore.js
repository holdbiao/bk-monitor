import Vue from 'vue'

export const state = Vue.observable({
  bizId: window.cc_biz_id,
  bizList: window.cc_biz_list || [],
  header: {
    backTitle: '',
    title: '',
    handlBack() {

    }
  },
  toggle: false
})

export const mutations = {
  setBackTitle(title) {
    state.header.backTitle = title
  },
  setTitle(title) {
    state.header.title = title
  },
  setBack(callBack) {
    state.header.handlBack = callBack
  },
  setToggle(toggle) {
    state.toggle = toggle
  }
}
export const getters = {
  bizId: state.bizId,
  bizList: state.bizList,
  toggle: state.toggle
}
