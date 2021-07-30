import { Component, Vue } from 'vue-property-decorator'

// 根据每个列表页面设置统一的pageSize 并保存
@Component
export default class commonPageSizeMixin extends Vue {
  public handleSetCommonPageSize(pageSize = '10') {
    localStorage.setItem('__common_page_size__', pageSize)
  }
  public handleGetCommonPageSize() {
    return +localStorage.getItem('__common_page_size__') || 10
  }
}
